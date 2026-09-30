import base64
import binascii
import csv
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.sqlalchemy_define import get_session_factory


# 旧系统连接信息。会话 Cookie 必须由运行环境注入，避免凭证进入代码仓库。
LEGACY_SYSTEM_BASE_URL = os.getenv(
    "LEGACY_SYSTEM_BASE_URL",
    "https://gzjsjy.s1.office7x.cn",
).strip().rstrip("/")
URL = os.getenv(
    "LEGACY_SYSTEM_URL",
    f"{LEGACY_SYSTEM_BASE_URL}/SOA/WorkSpace.phtml",
).strip()
PHPSESSID = os.getenv("PHPSESSID", "").strip()
LEGACY_DS_CODE = os.getenv("LEGACY_DS_CODE", "").strip()
LEGACY_GROUP_ID = os.getenv("LEGACY_GROUP_ID")
VERIFY_TLS = os.getenv("LEGACY_VERIFY_TLS", "1") == "1"

DATASET_CONFIG = {
    "consignment": {
        "data_file": "Apps/Custom_logisticsAccountingPublicitySystem/ConsignmentBooking",
        "referer": f"{LEGACY_SYSTEM_BASE_URL}/Apps/Custom_logisticsAccountingPublicitySystem/ConsignmentBooking_index.phtml",
        "ds_code": "T0020142",
        "group_id": "",
        "checkpoint": "trade_ingest_checkpoint.json",
    },
    "performance": {
        "data_file": "Apps/Custom_logisticsAccountingPublicitySystem/PerformanceStatement",
        "referer": f"{LEGACY_SYSTEM_BASE_URL}/Apps/Custom_logisticsAccountingPublicitySystem/PerformanceStatement_index.phtml",
        "ds_code": "T00200DE",
        "group_id": "-1:0",
        "checkpoint": "performance_ingest_checkpoint.json",
    },
}

DATASET_TYPE = os.getenv("DATASET_TYPE", "consignment").strip().lower()
if DATASET_TYPE not in DATASET_CONFIG:
    DATASET_TYPE = "consignment"

# 浏览器相关的 Sec-Fetch 和 sec-ch-ua 不是接口业务参数，这里只保留必要请求头。
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": LEGACY_SYSTEM_BASE_URL,
    "Referer": DATASET_CONFIG[DATASET_TYPE]["referer"],
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 "
        "Safari/537.36 Edg/151.0.0.0"
    ),
}

# 基础数据模板
BASE_DATA = {
    "OPtion": "",
    "DataFile": "Apps/Custom_logisticsAccountingPublicitySystem/ConsignmentBooking",
    "Action": "Ow==",
    "dsCode": LEGACY_DS_CODE or DATASET_CONFIG[DATASET_TYPE]["ds_code"],
    "IDList": [],
    # 旧系统接口字段本身拼写为 Serch，必须与浏览器请求保持一致。
    "Serch": {},
    "DispStyle": "datagrid",
    "SortType": [],
    "filterData": [],
    "PageRows": max(1, int(os.getenv("PAGE_ROWS", "50"))),
    "PageNo": 1,  # 初始页码
    "GroupID": (
        LEGACY_GROUP_ID.strip()
        if LEGACY_GROUP_ID is not None
        else DATASET_CONFIG[DATASET_TYPE]["group_id"]
    ),
    "ShortGID": "",
    "SubGroupData": 0
}
BASE_DATA["DataFile"] = DATASET_CONFIG[DATASET_TYPE]["data_file"]

# 自动翻页配置（默认关闭）
ENABLE_AUTO_PAGING = os.getenv("ENABLE_AUTO_PAGING", "0") == "1"
AUTO_MAX_PAGES = int(os.getenv("AUTO_MAX_PAGES", "0"))  # 0 表示不限制
AUTO_RESUME = os.getenv("AUTO_RESUME", "1") == "1"
AUTO_INTERVAL_SECONDS = float(os.getenv("AUTO_INTERVAL_SECONDS", "0.2"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
REQUEST_MAX_RETRIES = max(0, int(os.getenv("REQUEST_MAX_RETRIES", "3")))
REQUEST_RETRY_INTERVAL_SECONDS = float(os.getenv("REQUEST_RETRY_INTERVAL_SECONDS", "1.5"))
START_PAGE = max(1, int(os.getenv("START_PAGE", "1")))
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
EXPORT_CSV = os.getenv("EXPORT_CSV", "1" if DRY_RUN else "0") == "1"
PRINT_RESPONSE = os.getenv("PRINT_RESPONSE", "0") == "1"
OUTPUT_DIR = Path(
    os.getenv("INGEST_OUTPUT_DIR", str(Path(__file__).resolve().parent / "output"))
).expanduser()
CHECKPOINT_FILE = OUTPUT_DIR / DATASET_CONFIG[DATASET_TYPE]["checkpoint"]


def build_payload(page_num):
    """构造请求体并进行 Base64 编码"""
    current_data = BASE_DATA.copy()
    current_data["PageNo"] = page_num

    json_str = json.dumps(current_data, ensure_ascii=False)
    return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")


def decode_json_str_response(response_text):
    """解析形如 JsonStr:xxxxx 的响应内容，并尽量转成可读格式"""
    if not response_text:
        return None, "空响应"

    match = re.search(r"JsonStr:\s*(.+)", response_text, flags=re.DOTALL)
    if not match:
        return None, "响应中未找到 JsonStr: 前缀"

    base64_text = re.sub(r"\s+", "", match.group(1))
    if not base64_text:
        return None, "JsonStr: 后面没有可解码内容"

    padding = (-len(base64_text)) % 4
    if padding:
        base64_text += "=" * padding

    try:
        decoded_bytes = base64.b64decode(base64_text)
    except (binascii.Error, ValueError) as exc:
        return None, f"Base64 解码失败: {exc}"

    decoded_text = decoded_bytes.decode("utf-8", errors="replace")
    try:
        parsed_json = json.loads(decoded_text)
        return parsed_json, None
    except json.JSONDecodeError:
        return decoded_text, "Base64 已解码，但不是合法 JSON"


def format_response(response_text):
    """将接口响应转成可读字符串"""
    parsed_data, warning = decode_json_str_response(response_text)

    if parsed_data is None:
        parts = []
        if warning:
            parts.append(f"[解析提示] {warning}")
        parts.append("[原始响应]")
        parts.append(response_text)
        return "\n".join(parts)

    parts = []
    if warning:
        parts.append(f"[解析提示] {warning}")

    if isinstance(parsed_data, (dict, list)):
        parts.append("[解码后的 JSON]")
        parts.append(json.dumps(parsed_data, ensure_ascii=False, indent=2))
    else:
        parts.append("[解码后的文本]")
        parts.append(str(parsed_data))

    return "\n".join(parts)


def extract_csv_dataset(parsed_json):
    """根据 TableTitle 和 DataList 提取 CSV 表头和数据行"""
    if not isinstance(parsed_json, dict):
        return [], []

    headers_meta = parsed_json.get("TableTitle") or []
    if not isinstance(headers_meta, list):
        return [], []

    headers_meta = sorted(
        [item for item in headers_meta if isinstance(item, dict)],
        key=lambda item: item.get("colID", 0),
    )
    headers = [
        item.get("FieldName") or item.get("FieldID") or ""
        for item in headers_meta
    ]

    rows = []
    data_list = parsed_json.get("DataList") or []
    for row_item in data_list:
        if not isinstance(row_item, list):
            continue

        raw_values = row_item[2] if len(row_item) > 2 and isinstance(row_item[2], list) else []
        rendered_cells = row_item[3:] if len(row_item) > 3 else []
        row_data = []

        for idx, header_meta in enumerate(headers_meta):
            value = ""

            if idx < len(rendered_cells) and isinstance(rendered_cells[idx], dict):
                value = rendered_cells[idx].get("Text")

            if (value is None or value == "") and raw_values:
                col_id = header_meta.get("colID")
                if isinstance(col_id, int) and 0 <= col_id < len(raw_values):
                    value = raw_values[col_id]

            row_data.append("" if value is None else str(value))

        rows.append(row_data)

    return headers, rows


def write_csv(file_path, headers, rows):
    """写入 CSV 文件，返回写入的行数"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        if headers:
            writer.writerow(headers)
        writer.writerows(rows)
    return len(rows)


def export_page_csv(parsed_json):
    """把当前页原始表格导出为 CSV，便于入库前人工检查。"""
    headers, rows = extract_csv_dataset(parsed_json)
    if not headers:
        return None, 0
    page_no = parsed_json.get("PageNo", 1)
    csv_path = OUTPUT_DIR / f"{DATASET_TYPE}_page_{page_no}.csv"
    return csv_path, write_csv(csv_path, headers, rows)


def extract_trade_records(parsed_json):
    """将接口数据提取为结构化记录，便于入库分析"""
    headers, rows = extract_csv_dataset(parsed_json)
    data_list = parsed_json.get("DataList") or [] if isinstance(parsed_json, dict) else []
    page_no = parsed_json.get("PageNo", 1) if isinstance(parsed_json, dict) else 1

    records = []
    for idx, row_values in enumerate(rows):
        row_item = data_list[idx] if idx < len(data_list) and isinstance(data_list[idx], list) else []
        row_uuid = row_item[0] if row_item else ""
        row_map = dict(zip(headers, row_values))
        row_map["row_uuid"] = row_uuid
        row_map["source_page_no"] = page_no
        row_map["raw_row_json"] = json.dumps(row_item, ensure_ascii=False)
        records.append(row_map)

    return records


def save_records_to_db(records):
    """写入 MySQL（按排单编号去重更新）"""
    if not records:
        return 0

    sql = text(
        """
        INSERT INTO t_consignment_trade (
            order_no,
            row_uuid,
            scheduling_time,
            shipping_channel,
            salesman,
            shipping_customer,
            shipping_code,
            shipping_date,
            scheduling_status,
            shipper,
            delivery_time,
            receiving_address,
            go_upstairs,
            logistics_tracking,
            settlement_status,
            payment_status,
            payment_method,
            remark,
            source_page_no,
            raw_row_json
        ) VALUES (
            :order_no,
            :row_uuid,
            :scheduling_time,
            :shipping_channel,
            :salesman,
            :shipping_customer,
            :shipping_code,
            :shipping_date,
            :scheduling_status,
            :shipper,
            :delivery_time,
            :receiving_address,
            :go_upstairs,
            :logistics_tracking,
            :settlement_status,
            :payment_status,
            :payment_method,
            :remark,
            :source_page_no,
            :raw_row_json
        )
        ON DUPLICATE KEY UPDATE
            row_uuid = VALUES(row_uuid),
            scheduling_time = VALUES(scheduling_time),
            shipping_channel = VALUES(shipping_channel),
            salesman = VALUES(salesman),
            shipping_customer = VALUES(shipping_customer),
            shipping_code = VALUES(shipping_code),
            shipping_date = VALUES(shipping_date),
            scheduling_status = VALUES(scheduling_status),
            shipper = VALUES(shipper),
            delivery_time = VALUES(delivery_time),
            receiving_address = VALUES(receiving_address),
            go_upstairs = VALUES(go_upstairs),
            logistics_tracking = VALUES(logistics_tracking),
            settlement_status = VALUES(settlement_status),
            payment_status = VALUES(payment_status),
            payment_method = VALUES(payment_method),
            remark = VALUES(remark),
            source_page_no = VALUES(source_page_no),
            raw_row_json = VALUES(raw_row_json),
            updated_at = CURRENT_TIMESTAMP
        """
    )

    params = []
    for item in records:
        order_no = (item.get("排单编号") or "").strip()
        if not order_no:
            continue
        params.append(
            {
                "order_no": order_no,
                "row_uuid": item.get("row_uuid") or None,
                "scheduling_time": item.get("排单时间") or None,
                "shipping_channel": item.get("托运渠道") or None,
                "salesman": item.get("业务员") or None,
                "shipping_customer": item.get("托运客户") or None,
                "shipping_code": item.get("托运编码") or None,
                "shipping_date": item.get("出货日期") or None,
                "scheduling_status": item.get("调度状态") or None,
                "shipper": item.get("发货人") or None,
                "delivery_time": item.get("托运日期") or None,
                "receiving_address": item.get("收货地址") or None,
                "go_upstairs": item.get("是否上楼") or None,
                "logistics_tracking": item.get("物流跟踪") or None,
                "settlement_status": item.get("结算状态") or None,
                "payment_status": item.get("收款状态") or None,
                "payment_method": item.get("收款方式") or None,
                "remark": item.get("备注说明") or None,
                "source_page_no": item.get("source_page_no") or 1,
                "raw_row_json": item.get("raw_row_json") or "[]",
            }
        )

    if not params:
        return 0

    session = get_session_factory()()
    try:
        session.execute(sql, params)
        session.commit()
        return len(params)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def parse_amount(value):
    if value is None:
        return None
    text_value = str(value).strip()
    if not text_value:
        return None
    matched = re.search(r"-?\d+(?:\.\d+)?", text_value.replace(",", ""))
    return float(matched.group(0)) if matched else None


def parse_unit_number(value):
    return parse_amount(value)


def parse_date(value):
    if value is None:
        return None
    text_value = str(value).strip()
    if not text_value:
        return None
    matched = re.search(r"\d{4}-\d{2}-\d{2}", text_value)
    return matched.group(0) if matched else None


def build_performance_record_key(row_uuid, row_map, raw_row_json):
    """绩效表优先用公司单号，其次托运编号，最后回退"""
    company_no = (row_map.get("公司单号") or "").strip()
    if company_no:
        return company_no

    shipping_no = (row_map.get("托运编号") or "").strip()
    shipping_date = (row_map.get("托运日期") or "").strip()
    if shipping_no:
        return f"{shipping_no}|{shipping_date}"

    if row_uuid:
        return str(row_uuid)
    return hashlib.md5(raw_row_json.encode("utf-8")).hexdigest()


def extract_performance_records(parsed_json):
    """将 PerformanceStatement 提取为结构化字段"""
    headers, rows = extract_csv_dataset(parsed_json)
    data_list = parsed_json.get("DataList") or [] if isinstance(parsed_json, dict) else []
    page_no = parsed_json.get("PageNo", 1) if isinstance(parsed_json, dict) else 1

    records = []
    for idx, row_values in enumerate(rows):
        row_item = data_list[idx] if idx < len(data_list) and isinstance(data_list[idx], list) else []
        row_uuid = row_item[0] if row_item else ""
        row_map = dict(zip(headers, row_values))
        raw_row_json = json.dumps(row_item, ensure_ascii=False)

        gc_val = parse_unit_number(row_map.get("货物件数"))
        goods_count_val = int(gc_val) if gc_val is not None else 0

        records.append(
            {
                "record_key": build_performance_record_key(row_uuid=row_uuid, row_map=row_map, raw_row_json=raw_row_json),
                "row_uuid": row_uuid,
                "source_page_no": page_no,
                "order_id": row_map.get("系统内部ID") or row_map.get("order_id") or None,
                "shipping_date": parse_date(row_map.get("托运日期")),
                "shipping_channel": row_map.get("托运渠道") or None,
                "salesman": row_map.get("业务员") or None,
                "shipping_no": row_map.get("托运编号") or row_map.get("托运号码") or None,
                "follow_up_no": row_map.get("跟进编码") or row_map.get("跟单码") or None,
                "shipping_cost": parse_amount(row_map.get("托运成本")),
                "deduct_cost": parse_amount(row_map.get("扣除成本")),
                "shipping_fee": parse_amount(row_map.get("运费") or row_map.get("托运费")),
                "invoice_fee": parse_amount(row_map.get("开票费")),
                "adjust_profit": parse_amount(row_map.get("调整利润")),
                "forklift_fee": parse_amount(row_map.get("叉车费")),
                "pallet_fee": parse_amount(row_map.get("卡板费")),
                "ad_fee": parse_amount(row_map.get("广告费")),
                "huolala_fee": parse_amount(row_map.get("货拉拉") or row_map.get("货拉拉费用")),
                "pickup_fee": parse_amount(row_map.get("提货费")),
                "advance_freight_fee": parse_amount(row_map.get("代付运费")),
                "advance_misc_fee": parse_amount(row_map.get("代付杂费")),
                "other_fee": parse_amount(row_map.get("其它") or row_map.get("其他费用")),
                "reimbursement_amount": parse_amount(row_map.get("报销金额")),
                "actual_performance": parse_amount(row_map.get("实际业绩") or row_map.get("实际业绩(利润)")),
                "payment_status": row_map.get("收款状态") or None,
                "payment_method": row_map.get("付款方式") or row_map.get("收款方式") or None,
                "payment_date": parse_date(row_map.get("收款日期")),
                "reconciliation_date": parse_date(row_map.get("对账日期")),
                "salesman_payment_date": parse_date(row_map.get("业务员收款日期")),
                "company_tracking_no": row_map.get("公司单号") or None,
                "ship_to": row_map.get("送货地址") or row_map.get("收货单位") or None,
                "product_name": row_map.get("货品名称") or row_map.get("产品名称") or None,
                "goods_count": goods_count_val,
                "goods_weight": parse_unit_number(row_map.get("货物重量") or row_map.get("重量(KG)")),
                "goods_volume": parse_unit_number(row_map.get("货物体积") or row_map.get("体积(CBM)")),
                "remark": row_map.get("排单备注") or row_map.get("备注") or None,
                "row_text_json": json.dumps(row_map, ensure_ascii=False),
                "raw_row_json": raw_row_json,
            }
        )
    return records



def save_performance_records_to_db(records):
    """写入 PerformanceStatement 表（按 record_key 去重更新）"""
    if not records:
        return 0

    sql = text(
        """
        INSERT INTO t_performance_statement (
            record_key,
            row_uuid,
            source_page_no,
            order_id,
            shipping_date,
            shipping_channel,
            salesman,
            shipping_no,
            follow_up_no,
            shipping_cost,
            deduct_cost,
            shipping_fee,
            invoice_fee,
            adjust_profit,
            forklift_fee,
            pallet_fee,
            ad_fee,
            huolala_fee,
            pickup_fee,
            advance_freight_fee,
            advance_misc_fee,
            other_fee,
            reimbursement_amount,
            actual_performance,
            payment_status,
            payment_method,
            payment_date,
            reconciliation_date,
            salesman_payment_date,
            company_tracking_no,
            ship_to,
            product_name,
            goods_count,
            goods_weight,
            goods_volume,
            remark,
            row_text_json,
            raw_row_json
        ) VALUES (
            :record_key,
            :row_uuid,
            :source_page_no,
            :order_id,
            :shipping_date,
            :shipping_channel,
            :salesman,
            :shipping_no,
            :follow_up_no,
            :shipping_cost,
            :deduct_cost,
            :shipping_fee,
            :invoice_fee,
            :adjust_profit,
            :forklift_fee,
            :pallet_fee,
            :ad_fee,
            :huolala_fee,
            :pickup_fee,
            :advance_freight_fee,
            :advance_misc_fee,
            :other_fee,
            :reimbursement_amount,
            :actual_performance,
            :payment_status,
            :payment_method,
            :payment_date,
            :reconciliation_date,
            :salesman_payment_date,
            :company_tracking_no,
            :ship_to,
            :product_name,
            :goods_count,
            :goods_weight,
            :goods_volume,
            :remark,
            :row_text_json,
            :raw_row_json
        )
        ON DUPLICATE KEY UPDATE
            row_uuid = VALUES(row_uuid),
            source_page_no = VALUES(source_page_no),
            order_id = VALUES(order_id),
            shipping_date = VALUES(shipping_date),
            shipping_channel = VALUES(shipping_channel),
            salesman = VALUES(salesman),
            shipping_no = VALUES(shipping_no),
            follow_up_no = VALUES(follow_up_no),
            shipping_cost = VALUES(shipping_cost),
            deduct_cost = VALUES(deduct_cost),
            shipping_fee = VALUES(shipping_fee),
            invoice_fee = VALUES(invoice_fee),
            adjust_profit = VALUES(adjust_profit),
            forklift_fee = VALUES(forklift_fee),
            pallet_fee = VALUES(pallet_fee),
            ad_fee = VALUES(ad_fee),
            huolala_fee = VALUES(huolala_fee),
            pickup_fee = VALUES(pickup_fee),
            advance_freight_fee = VALUES(advance_freight_fee),
            advance_misc_fee = VALUES(advance_misc_fee),
            other_fee = VALUES(other_fee),
            reimbursement_amount = VALUES(reimbursement_amount),
            actual_performance = VALUES(actual_performance),
            payment_status = VALUES(payment_status),
            payment_method = VALUES(payment_method),
            payment_date = VALUES(payment_date),
            reconciliation_date = VALUES(reconciliation_date),
            salesman_payment_date = VALUES(salesman_payment_date),
            company_tracking_no = VALUES(company_tracking_no),
            ship_to = VALUES(ship_to),
            product_name = VALUES(product_name),
            goods_count = VALUES(goods_count),
            goods_weight = VALUES(goods_weight),
            goods_volume = VALUES(goods_volume),
            remark = VALUES(remark),
            row_text_json = VALUES(row_text_json),
            raw_row_json = VALUES(raw_row_json),
            updated_at = CURRENT_TIMESTAMP
        """
    )

    session = get_session_factory()()
    try:
        session.execute(sql, records)
        session.commit()
        return len(records)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def load_checkpoint(checkpoint_file=None):
    checkpoint_file = checkpoint_file or CHECKPOINT_FILE
    if not checkpoint_file.exists():
        return None
    try:
        with open(checkpoint_file, "r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
            if isinstance(data, dict):
                return data
    except Exception:
        return None
    return None


def save_checkpoint(page_no, total_pages=None, checkpoint_file=None):
    checkpoint_file = checkpoint_file or CHECKPOINT_FILE
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_success_page": page_no,
        "total_pages": total_pages,
        "updated_at": int(time.time()),
    }
    with open(checkpoint_file, "w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=2)


def clear_checkpoint(checkpoint_file=None):
    checkpoint_file = checkpoint_file or CHECKPOINT_FILE
    if checkpoint_file.exists():
        checkpoint_file.unlink()


def run_paginated_ingest(start_page=1, max_pages=0, resume=True):
    """自动翻页抓取，并按运行模式预览或入库。"""
    # 预览不能推进正式入库断点，否则切换 DRY_RUN=0 后会跳过已预览的页面。
    checkpoint = load_checkpoint() if resume and not DRY_RUN else None
    if checkpoint and isinstance(checkpoint.get("last_success_page"), int):
        start_page = max(start_page, checkpoint["last_success_page"] + 1)

    if DRY_RUN:
        mode = "预览并导出 CSV" if EXPORT_CSV else "只预览，不入库"
    else:
        mode = "入库并导出 CSV" if EXPORT_CSV else "只入库，不导出 CSV"
    print(
        f"自动翻页启动，数据集: {DATASET_TYPE}，模式: {mode}，"
        f"起始页: {start_page}，最大页数限制: {max_pages or '不限制'}"
    )
    page_no = start_page
    processed_pages = 0
    total_saved = 0

    while True:
        if max_pages > 0 and processed_pages >= max_pages:
            print("达到 AUTO_MAX_PAGES 限制，停止自动翻页。")
            break

        raw_result = fetch_page(page_no)
        if not raw_result:
            print(f"第 {page_no} 页请求失败，停止自动翻页。")
            break

        parsed_data, warning = decode_json_str_response(raw_result)
        if warning:
            print(f"第 {page_no} 页解析提示: {warning}")
        if not isinstance(parsed_data, dict):
            print(f"第 {page_no} 页解析失败（非 JSON 对象），停止自动翻页。")
            break

        headers, _ = extract_csv_dataset(parsed_data)
        if not headers:
            print(f"第 {page_no} 页没有可导出的表头，停止自动翻页。")
            break

        if EXPORT_CSV:
            csv_path, csv_rows = export_page_csv(parsed_data)
            print(f"第 {page_no} 页 CSV 已生成: {csv_path}（{csv_rows} 条）")

        records = (
            extract_performance_records(parsed_data)
            if DATASET_TYPE == "performance"
            else extract_trade_records(parsed_data)
        )
        if DRY_RUN:
            saved_count = 0
        elif DATASET_TYPE == "performance":
            saved_count = save_performance_records_to_db(records) if records else 0
        else:
            saved_count = save_records_to_db(records) if records else 0
        total_saved += saved_count

        current_page = parsed_data.get("PageNo", page_no)
        total_pages = parsed_data.get("Pages")
        data_list = parsed_data.get("DataList") or []

        if not DRY_RUN:
            save_checkpoint(current_page, total_pages)
        processed_pages += 1
        if DRY_RUN:
            print(f"第 {current_page} 页检查完成，DRY_RUN 未写数据库。")
        else:
            print(f"第 {current_page} 页入库完成，写入/更新 {saved_count} 条。")

        if isinstance(total_pages, int) and current_page >= total_pages:
            print(f"已到最后一页（{current_page}/{total_pages}），自动翻页结束。")
            if not DRY_RUN:
                clear_checkpoint()
            break

        if not data_list:
            print(f"第 {current_page} 页无数据，自动翻页结束。")
            if not DRY_RUN:
                clear_checkpoint()
            break

        page_no = current_page + 1
        if AUTO_INTERVAL_SECONDS > 0:
            time.sleep(AUTO_INTERVAL_SECONDS)

    print(f"自动翻页结束，共处理 {processed_pages} 页，累计写入/更新 {total_saved} 条。")


def fetch_page(page_num=1):
    if not PHPSESSID:
        raise RuntimeError("缺少 PHPSESSID 环境变量，请先从旧系统登录会话中取得 Cookie。")

    payload = build_payload(page_num)
    headers = HEADERS.copy()
    headers["Referer"] = DATASET_CONFIG[DATASET_TYPE]["referer"]

    total_attempts = REQUEST_MAX_RETRIES + 1
    for attempt in range(1, total_attempts + 1):
        try:
            response = requests.post(
                URL,
                headers=headers,
                cookies={"PHPSESSID": PHPSESSID},
                data=payload,
                verify=VERIFY_TLS,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )

            print(f"第 {page_num} 页响应状态码: {response.status_code}")
            if response.status_code == 200:
                return response.text

            retryable = response.status_code == 429 or response.status_code >= 500
            if not retryable or attempt >= total_attempts:
                print(f"第 {page_num} 页请求失败，状态码: {response.status_code}")
                return None
            print(f"第 {page_num} 页请求失败，{REQUEST_RETRY_INTERVAL_SECONDS} 秒后重试（{attempt}/{REQUEST_MAX_RETRIES}）。")
        except requests.RequestException as exc:
            if attempt >= total_attempts:
                print(f"请求发生异常，已达到最大重试次数: {exc}")
                return None
            print(f"请求发生异常: {exc}，{REQUEST_RETRY_INTERVAL_SECONDS} 秒后重试（{attempt}/{REQUEST_MAX_RETRIES}）。")

        if REQUEST_RETRY_INTERVAL_SECONDS > 0:
            time.sleep(REQUEST_RETRY_INTERVAL_SECONDS)

    return None


def main():
    if not PHPSESSID:
        print("缺少 PHPSESSID 环境变量，请先从旧系统登录会话中取得 Cookie。")
        return

    if ENABLE_AUTO_PAGING:
        run_paginated_ingest(
            start_page=START_PAGE,
            max_pages=AUTO_MAX_PAGES,
            resume=AUTO_RESUME,
        )
        return

    page_num = START_PAGE
    if DRY_RUN:
        mode = "预览并导出 CSV" if EXPORT_CSV else "只预览，不入库"
    else:
        mode = "入库并导出 CSV" if EXPORT_CSV else "只入库，不导出 CSV"
    print(f"当前数据集: {DATASET_TYPE} ({BASE_DATA.get('DataFile')})")
    print(f"运行模式: {mode}")
    print(f"开始请求第 {page_num} 页...")

    result = fetch_page(page_num)
    if not result:
        print("没有获取到结果，请检查 Cookie、网络或请求参数。")
        return

    if PRINT_RESPONSE:
        print("===== 格式化结果开始 =====")
        print(format_response(result))
        print("===== 格式化结果结束 =====")

    parsed_data, warning = decode_json_str_response(result)
    if warning:
        print(f"解析提示: {warning}")
    if not isinstance(parsed_data, dict):
        print("解码结果不是 JSON 对象，无法继续处理。")
        return

    headers, _ = extract_csv_dataset(parsed_data)
    if not headers:
        print("未找到可用表头，无法继续处理。")
        return

    if EXPORT_CSV:
        csv_path, row_count = export_page_csv(parsed_data)
        print(f"CSV 已生成: {csv_path}")
        print(f"CSV 数据行数: {row_count}")

    records = (
        extract_performance_records(parsed_data)
        if DATASET_TYPE == "performance"
        else extract_trade_records(parsed_data)
    )

    if DRY_RUN:
        print(f"DRY_RUN 检查完成：解析 {len(records)} 条，数据库未写入。")
        return

    try:
        if DATASET_TYPE == "performance":
            saved_count = save_performance_records_to_db(records)
            print(f"PerformanceStatement 入库完成: {saved_count} 条（按 record_key 去重）")
        else:
            saved_count = save_records_to_db(records)
            print(f"数据库写入完成: {saved_count} 条（按排单编号去重）")
    except Exception as exc:
        print(f"数据库写入失败: {exc}")


if __name__ == "__main__":
    main()
