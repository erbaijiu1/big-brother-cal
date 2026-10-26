from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
import re
from statistics import median
from typing import Any, Iterable, Optional

from tool.product_category_normalizer import PRODUCT_CATEGORIES


CANONICAL_CATEGORIES = PRODUCT_CATEGORIES
UNKNOWN_CATEGORY = "未知品类"
PENDING_CATEGORY = "待归一"
UNKNOWN_SALESMAN = "未识别业务员"
UNKNOWN_CUSTOMER = "未识别客户"
UNKNOWN_GROUP_KEY = "__UNKNOWN__"


def _number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _round(value: float, digits: int = 2) -> float:
    return round(value, digits)


def normalize_category(product_name: Optional[str]) -> str:
    name = (product_name or "").strip()
    if not name:
        return UNKNOWN_CATEGORY
    if name in CANONICAL_CATEGORIES:
        return name
    return PENDING_CATEGORY


def prepare_order(raw: dict[str, Any]) -> dict[str, Any]:
    shipping_fee = _number(raw.get("shipping_fee"))
    shipping_cost = _number(raw.get("shipping_cost"))
    missing_cost = shipping_fee > 0 and shipping_cost == 0
    customer = (raw.get("shipping_customer") or "").strip() or None
    product_name = (raw.get("product_name") or "").strip()

    return {
        **raw,
        "shipping_fee": shipping_fee,
        "shipping_cost": shipping_cost,
        "gross_profit": None if missing_cost else shipping_fee - shipping_cost,
        "missing_cost": missing_cost,
        "shipping_customer": customer,
        "customer_identifiable": customer is not None,
        "product_name": product_name,
        "category": normalize_category(product_name),
    }


def _order_key(order: dict[str, Any]) -> tuple[Any, str, int]:
    return (
        order["shipping_date"],
        str(order.get("company_tracking_no") or ""),
        int(order.get("id") or 0),
    )


def _sum_profit(orders: Iterable[dict[str, Any]]) -> float:
    return sum(order["gross_profit"] for order in orders if order["gross_profit"] is not None)


def _valid_revenue(orders: Iterable[dict[str, Any]]) -> float:
    return sum(order["shipping_fee"] for order in orders if not order["missing_cost"])


def _profit_rate(orders: list[dict[str, Any]]) -> Optional[float]:
    revenue = _valid_revenue(orders)
    if revenue <= 0:
        return None
    return _round(_sum_profit(orders) / revenue * 100)


def _pct(numerator: float, denominator: float) -> Optional[float]:
    if denominator <= 0:
        return None
    return _round(numerator / denominator * 100)


def _profit_share(profit: float, denominator: float) -> Optional[float]:
    """Net-profit share; undefined when the filtered net-profit pool is not positive."""
    return _pct(profit, denominator) if denominator > 0 else None


def _concentration(rows: list[dict[str, Any]], top_n: int, denominator: float) -> Optional[float]:
    if denominator <= 0:
        return None
    ranked_profit = sorted((row["total_profit"] for row in rows), reverse=True)
    return _pct(sum(ranked_profit[:top_n]), denominator)


def _customer_history(orders: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    history: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in orders:
        customer = order["shipping_customer"]
        if customer:
            history[customer].append(order)

    first_orders: dict[str, dict[str, Any]] = {}
    for customer, customer_orders in history.items():
        customer_orders.sort(key=_order_key)
        first_orders[customer] = customer_orders[0]
    return first_orders, history


def _category_first_orders(history: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], dict[str, Any]]:
    category_first: dict[tuple[str, str], dict[str, Any]] = {}
    for customer, customer_orders in history.items():
        for order in customer_orders:
            if order["category"] not in CANONICAL_CATEGORIES:
                continue
            category_first.setdefault((customer, order["category"]), order)
    return category_first


def _cohort_metrics(
    customers: list[str],
    first_orders: dict[str, dict[str, Any]],
    history: dict[str, list[dict[str, Any]]],
    cutoff: date,
    days: int,
) -> dict[str, Any]:
    mature = [customer for customer in customers if first_orders[customer]["shipping_date"] <= cutoff - timedelta(days=days)]
    repurchased = 0
    same_category_repurchased = 0
    cumulative_profit = 0.0
    profit_covered_orders = 0
    total_window_orders = 0

    for customer in mature:
        first = first_orders[customer]
        first_key = _order_key(first)
        window_end = first["shipping_date"] + timedelta(days=days)
        window_orders = [
            order for order in history[customer]
            if first["shipping_date"] <= order["shipping_date"] <= window_end
        ]
        follow_ups = [order for order in window_orders if _order_key(order) > first_key]
        if follow_ups:
            repurchased += 1
        if any(order["category"] == first["category"] for order in follow_ups):
            same_category_repurchased += 1
        cumulative_profit += _sum_profit(window_orders)
        profit_covered_orders += sum(order["gross_profit"] is not None for order in window_orders)
        total_window_orders += len(window_orders)

    return {
        "days": days,
        "mature_customers": len(mature),
        "repurchased_customers": repurchased,
        "repurchase_rate_pct": _pct(repurchased, len(mature)),
        "same_category_repurchase_rate_pct": _pct(same_category_repurchased, len(mature)),
        "cumulative_profit_per_customer": _round(cumulative_profit / len(mature)) if mature else None,
        "profit_order_coverage_pct": _pct(profit_covered_orders, total_window_orders),
        "sample_sufficient": len(mature) >= 5,
    }


def _candidate_status(metric: dict[str, Any], min_orders: int, min_new_customers: int, max_negative_rate: float) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if metric["order_count"] < min_orders or metric["database_first_customer_count"] < min_new_customers:
        reasons.append(f"样本不足：需≥{min_orders}票且≥{min_new_customers}名新客")
        return "需要观察", reasons
    if (metric["avg_database_first_order_profit"] or 0) <= 0:
        reasons.append("新客首单平均毛利润不为正")
        return "暂不建议投放", reasons
    if (metric["negative_profit_rate_pct"] or 0) > max_negative_rate:
        reasons.append(f"负毛利票占比超过{max_negative_rate:g}%")
        return "暂不建议投放", reasons
    if metric["total_profit"] <= 0:
        reasons.append("品类总毛利润不为正")
        return "暂不建议投放", reasons
    if metric["cohort_90"]["mature_customers"] >= min_new_customers and (metric["cohort_90"]["repurchase_rate_pct"] or 0) > 0:
        reasons.extend(["首单毛利润为正", "有持续新客进入", "90天成熟新客出现复购"])
        return "值得测试", reasons
    reasons.extend(["当前盈利为正", "90天成熟样本或复购证据仍不足"])
    return "需要观察", reasons


def build_acquisition_analysis(
    raw_rows: Iterable[dict[str, Any]],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    identifiable_only: bool = False,
    new_customers_only: bool = False,
    min_orders: int = 20,
    min_new_customers: int = 5,
    max_negative_rate: float = 30.0,
) -> dict[str, Any]:
    orders = [prepare_order(dict(row)) for row in raw_rows]
    if not orders:
        return {"summary": {}, "categories": [], "monthly": [], "quality": {}, "period": {}}

    data_start = min(order["shipping_date"] for order in orders)
    data_end = max(order["shipping_date"] for order in orders)
    end = min(end_date or data_end, data_end)
    start = start_date or end - timedelta(days=179)
    first_orders, history = _customer_history(orders)
    category_first_orders = _category_first_orders(history)

    selected = [order for order in orders if start <= order["shipping_date"] <= end]
    if category:
        selected = [order for order in selected if order["category"] == category]
    if channel:
        selected = [order for order in selected if (order.get("shipping_channel") or "").strip() == channel]
    if identifiable_only:
        selected = [order for order in selected if order["customer_identifiable"]]
    if new_customers_only:
        selected = [
            order for order in selected
            if order["shipping_customer"] and first_orders[order["shipping_customer"]]["id"] == order["id"]
        ]

    selected_ids = {order["id"] for order in selected}
    selected_first_customers = [
        customer for customer, first in first_orders.items()
        if first["id"] in selected_ids
    ]
    selected_first_orders = [first_orders[customer] for customer in selected_first_customers]
    covered_selected_first_orders = [order for order in selected_first_orders if order["gross_profit"] is not None]
    valid_profit_orders = [order for order in selected if order["gross_profit"] is not None]
    summary = {
        "order_count": len(selected),
        "total_revenue": _round(sum(order["shipping_fee"] for order in selected)),
        "total_profit": _round(_sum_profit(selected)),
        "profit_rate_pct": _profit_rate(selected),
        "identifiable_customer_count": len({order["shipping_customer"] for order in selected if order["shipping_customer"]}),
        "database_first_customer_count": len(selected_first_customers),
        "database_first_customer_profit": _round(_sum_profit(selected_first_orders)),
        "database_first_profit_covered_count": len(covered_selected_first_orders),
        "database_first_profit_coverage_pct": _pct(len(covered_selected_first_orders), len(selected_first_orders)),
        "avg_database_first_order_profit": _round(_sum_profit(covered_selected_first_orders) / len(covered_selected_first_orders))
        if covered_selected_first_orders else None,
        "missing_cost_order_count": sum(order["missing_cost"] for order in selected),
        "negative_profit_order_count": sum(order["gross_profit"] < 0 for order in valid_profit_orders),
        "profit_covered_order_count": len(valid_profit_orders),
        "profit_order_coverage_pct": _pct(len(valid_profit_orders), len(selected)),
        "profit_covered_revenue": _round(_valid_revenue(selected)),
        "profit_revenue_coverage_pct": _pct(_valid_revenue(selected), sum(order["shipping_fee"] for order in selected)),
    }

    overall_new_customer_count = len(selected_first_customers)
    category_metrics: list[dict[str, Any]] = []
    for category_name in CANONICAL_CATEGORIES:
        category_orders = [order for order in selected if order["category"] == category_name]
        if not category_orders:
            continue
        category_order_ids = {order["id"] for order in category_orders}
        category_new_customers = [
            customer for customer, first in first_orders.items()
            if first["id"] in category_order_ids
        ]
        category_first_customers = [
            customer for (customer, first_category), first in category_first_orders.items()
            if first_category == category_name and first["id"] in category_order_ids
        ]
        database_first_order_rows = [first_orders[customer] for customer in category_new_customers]
        category_first_order_rows = [category_first_orders[(customer, category_name)] for customer in category_first_customers]
        covered_database_first_orders = [order for order in database_first_order_rows if order["gross_profit"] is not None]
        covered_category_first_orders = [order for order in category_first_order_rows if order["gross_profit"] is not None]
        database_first_profit = _sum_profit(covered_database_first_orders)
        category_first_profit = _sum_profit(covered_category_first_orders)
        profit_values = [order["gross_profit"] for order in category_orders if order["gross_profit"] is not None]
        customer_count = len({order["shipping_customer"] for order in category_orders if order["shipping_customer"]})
        metric = {
            "category": category_name,
            "order_count": len(category_orders),
            "revenue": _round(sum(order["shipping_fee"] for order in category_orders)),
            "total_profit": _round(sum(profit_values)),
            "profit_rate_pct": _profit_rate(category_orders),
            "avg_order_profit": _round(sum(profit_values) / len(profit_values)) if profit_values else None,
            "median_order_profit": _round(median(profit_values)) if profit_values else None,
            "negative_profit_rate_pct": _pct(sum(value < 0 for value in profit_values), len(profit_values)),
            "missing_cost_order_count": sum(order["missing_cost"] for order in category_orders),
            "identifiable_customer_count": customer_count,
            "database_first_customer_count": len(category_new_customers),
            "database_first_customer_share_pct": _pct(len(category_new_customers), overall_new_customer_count),
            "database_first_order_profit": _round(database_first_profit),
            "database_first_profit_covered_count": len(covered_database_first_orders),
            "database_first_profit_coverage_pct": _pct(len(covered_database_first_orders), len(database_first_order_rows)),
            "avg_database_first_order_profit": _round(database_first_profit / len(covered_database_first_orders)) if covered_database_first_orders else None,
            "category_first_customer_count": len(category_first_customers),
            "category_first_customer_rate_pct": _pct(len(category_first_customers), customer_count),
            "category_first_order_profit": _round(category_first_profit),
            "category_first_profit_covered_count": len(covered_category_first_orders),
            "category_first_profit_coverage_pct": _pct(len(covered_category_first_orders), len(category_first_order_rows)),
            "avg_category_first_order_profit": _round(category_first_profit / len(covered_category_first_orders)) if covered_category_first_orders else None,
            "profit_order_coverage_pct": _pct(len(profit_values), len(category_orders)),
            "profit_revenue_coverage_pct": _pct(_valid_revenue(category_orders), sum(order["shipping_fee"] for order in category_orders)),
            "channel_count": len({(order.get("shipping_channel") or "").strip() for order in category_orders if (order.get("shipping_channel") or "").strip()}),
            "cohort_30": _cohort_metrics(category_new_customers, first_orders, history, end, 30),
            "cohort_90": _cohort_metrics(category_new_customers, first_orders, history, end, 90),
            "compliance_status": "待人工确认",
        }
        status, reasons = _candidate_status(metric, min_orders, min_new_customers, max_negative_rate)
        metric["candidate_status"] = status
        metric["candidate_reasons"] = reasons
        category_metrics.append(metric)

    category_metrics.sort(key=lambda item: (item["candidate_status"] != "值得测试", -item["total_profit"]))
    status_counts = Counter(item["candidate_status"] for item in category_metrics)

    monthly: list[dict[str, Any]] = []
    monthly_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for order in selected:
        if order["category"] in CANONICAL_CATEGORIES:
            monthly_groups[(order["shipping_date"].strftime("%Y-%m"), order["category"])].append(order)
    for (month, category_name), month_orders in sorted(monthly_groups.items()):
        month_ids = {order["id"] for order in month_orders}
        database_first_count = sum(first["id"] in month_ids for first in first_orders.values())
        category_first_count = sum(first["id"] in month_ids for first in category_first_orders.values())
        monthly.append({
            "month": month,
            "category": category_name,
            "order_count": len(month_orders),
            "database_first_customer_count": database_first_count,
            "category_first_customer_count": category_first_count,
            "total_profit": _round(_sum_profit(month_orders)),
            "avg_order_profit": _round(_sum_profit(month_orders) / len([o for o in month_orders if o["gross_profit"] is not None]))
            if any(order["gross_profit"] is not None for order in month_orders) else None,
        })

    matched_orders = [order for order in selected if order["customer_identifiable"]]
    quality = {
        "customer_match_order_count": len(matched_orders),
        "customer_match_rate_pct": _pct(len(matched_orders), len(selected)),
        "customer_match_revenue_pct": _pct(sum(order["shipping_fee"] for order in matched_orders), sum(order["shipping_fee"] for order in selected)),
        "pending_category_order_count": sum(order["category"] == PENDING_CATEGORY for order in selected),
        "pending_category_rate_pct": _pct(sum(order["category"] == PENDING_CATEGORY for order in selected), len(selected)),
        "unknown_category_order_count": sum(order["category"] == UNKNOWN_CATEGORY for order in selected),
        "unknown_category_rate_pct": _pct(sum(order["category"] == UNKNOWN_CATEGORY for order in selected), len(selected)),
        "missing_cost_order_count": summary["missing_cost_order_count"],
        "zero_revenue_order_count": sum(order["shipping_fee"] == 0 for order in selected),
        "negative_profit_order_count": summary["negative_profit_order_count"],
        "history_start_date": data_start.isoformat(),
        "history_end_date": data_end.isoformat(),
        "currency_status": "业务账单主币种未结构化",
        "duplicate_business_key_count": len(orders) - len({order["company_tracking_no"] for order in orders}),
        "cancellation_or_void_keyword_count": sum(
            bool(re.search(r"取消|作废", f"{order.get('product_name') or ''} {order.get('remark') or ''}", re.I))
            for order in selected
        ),
        "refund_or_reversal_keyword_count": sum(
            bool(re.search(r"退款|退费|冲销|冲账", f"{order.get('product_name') or ''} {order.get('remark') or ''}", re.I))
            for order in selected
        ),
        "compensation_or_supplement_keyword_count": sum(
            bool(re.search(r"赔付|赔款|补单", f"{order.get('product_name') or ''} {order.get('remark') or ''}", re.I))
            for order in selected
        ),
    }
    unknown_profit = _sum_profit(order for order in selected if order["category"] in {UNKNOWN_CATEGORY, PENDING_CATEGORY})
    quality["unclassified_profit_share_pct"] = _pct(unknown_profit, summary["total_profit"])

    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat(), "history_start_date": data_start.isoformat(), "history_end_date": data_end.isoformat()},
        "summary": summary,
        "categories": category_metrics,
        "monthly": monthly,
        "quality": quality,
        "candidate_status_counts": dict(status_counts),
        "thresholds": {"min_orders": min_orders, "min_new_customers": min_new_customers, "max_negative_rate_pct": max_negative_rate},
        "disclaimer": "历史新客活跃度不等于 Facebook 获客效率；当前未接入广告花费与归因数据。",
    }


def build_category_detail(
    analysis: dict[str, Any],
    raw_rows: Iterable[dict[str, Any]],
    category: str,
    channel: Optional[str] = None,
    salesman: Optional[str] = None,
) -> dict[str, Any]:
    metric = next((item for item in analysis["categories"] if item["category"] == category), None)
    if metric is None:
        return {}
    orders = [prepare_order(dict(row)) for row in raw_rows]
    start = date.fromisoformat(analysis["period"]["start_date"])
    end = date.fromisoformat(analysis["period"]["end_date"])
    category_orders = [order for order in orders if start <= order["shipping_date"] <= end and order["category"] == category]
    if channel:
        category_orders = [order for order in category_orders if (order.get("shipping_channel") or "").strip() == channel]

    first_orders, history = _customer_history(orders)
    selected_salesman_name: Optional[str] = None
    dimension_orders = category_orders
    if salesman:
        selected_salesman_name = UNKNOWN_SALESMAN if salesman == UNKNOWN_GROUP_KEY else salesman
        dimension_orders = [
            order for order in category_orders
            if ((order.get("salesman") or "").strip() or UNKNOWN_SALESMAN) == selected_salesman_name
        ]

    total_profit = _sum_profit(category_orders)
    dimension_revenue = sum(order["shipping_fee"] for order in dimension_orders)
    dimension_profit = _sum_profit(dimension_orders)

    channels: list[dict[str, Any]] = []
    channel_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in dimension_orders:
        channel_groups[(order.get("shipping_channel") or "").strip() or "未知渠道"].append(order)
    for name, channel_orders in channel_groups.items():
        channel_revenue = sum(order["shipping_fee"] for order in channel_orders)
        channel_profit = _sum_profit(channel_orders)
        channels.append({
            "name": name,
            "order_count": len(channel_orders),
            "revenue": _round(channel_revenue),
            "revenue_contribution_pct": _pct(channel_revenue, dimension_revenue),
            "total_profit": _round(channel_profit),
            "profit_contribution_pct": _profit_share(channel_profit, dimension_profit),
            "profit_rate_pct": _profit_rate(channel_orders),
        })
    channels.sort(key=lambda item: item["revenue"], reverse=True)

    salesman_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in category_orders:
        salesman_name = (order.get("salesman") or "").strip() or UNKNOWN_SALESMAN
        salesman_groups[salesman_name].append(order)

    salespeople: list[dict[str, Any]] = []
    for name, grouped_orders in salesman_groups.items():
        customer_names = {order["shipping_customer"] for order in grouped_orders if order["shipping_customer"]}
        grouped_ids = {order["id"] for order in grouped_orders}
        grouped_profit = _sum_profit(grouped_orders)
        salespeople.append({
            "key": UNKNOWN_GROUP_KEY if name == UNKNOWN_SALESMAN else name,
            "name": name,
            "order_count": len(grouped_orders),
            "customer_count": len(customer_names),
            "database_first_customer_count": sum(
                first_orders[customer]["id"] in grouped_ids for customer in customer_names
            ),
            "total_revenue": _round(sum(order["shipping_fee"] for order in grouped_orders)),
            "total_profit": _round(grouped_profit),
            "profit_contribution_pct": _profit_share(grouped_profit, total_profit),
            "profit_covered_order_count": sum(order["gross_profit"] is not None for order in grouped_orders),
        })
    salespeople.sort(key=lambda item: item["total_profit"], reverse=True)

    known_salespeople = [item for item in salespeople if item["key"] != UNKNOWN_GROUP_KEY]
    known_salesman_profit = sum(item["total_profit"] for item in known_salespeople)
    salesman_summary = {
        "salesman_count": len(known_salespeople),
        "unknown_order_count": len(salesman_groups.get(UNKNOWN_SALESMAN, [])),
        "profit_denominator": _round(known_salesman_profit),
        "top1_profit_concentration_pct": _concentration(known_salespeople, 1, known_salesman_profit),
        "top3_profit_concentration_pct": _concentration(known_salespeople, 3, known_salesman_profit),
    }

    customer_orders = dimension_orders

    customer_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in customer_orders:
        customer_name = order["shipping_customer"] or UNKNOWN_CUSTOMER
        customer_groups[customer_name].append(order)

    customer_profit_denominator = _sum_profit(customer_orders)
    customers: list[dict[str, Any]] = []
    for name, grouped_orders in customer_groups.items():
        grouped_profit = _sum_profit(grouped_orders)
        if name == UNKNOWN_CUSTOMER:
            first_date = None
            last_date = None
            is_database_first_customer = False
        else:
            full_history = history[name]
            first_date = first_orders[name]["shipping_date"].isoformat()
            last_date = max(order["shipping_date"] for order in full_history).isoformat()
            is_database_first_customer = first_orders[name]["id"] in {order["id"] for order in grouped_orders}
        customers.append({
            "key": UNKNOWN_GROUP_KEY if name == UNKNOWN_CUSTOMER else name,
            "name": name,
            "order_count": len(grouped_orders),
            "total_profit": _round(grouped_profit),
            "profit_contribution_pct": _profit_share(grouped_profit, customer_profit_denominator),
            "first_shipping_date": first_date,
            "last_shipping_date": last_date,
            "is_database_first_customer": is_database_first_customer,
            "profit_covered_order_count": sum(order["gross_profit"] is not None for order in grouped_orders),
        })
    customers.sort(key=lambda item: item["total_profit"], reverse=True)

    known_customers = [item for item in customers if item["key"] != UNKNOWN_GROUP_KEY]
    known_customer_profit = sum(item["total_profit"] for item in known_customers)
    largest_customer_profit = known_customers[0]["total_profit"] if known_customers else 0
    customer_summary = {
        "customer_count": len(known_customers),
        "unknown_order_count": len(customer_groups.get(UNKNOWN_CUSTOMER, [])),
        "profit_denominator": _round(known_customer_profit),
        "top1_profit_concentration_pct": _concentration(known_customers, 1, known_customer_profit),
        "top5_profit_concentration_pct": _concentration(known_customers, 5, known_customer_profit),
        "profit_excluding_largest_customer": _round(known_customer_profit - largest_customer_profit),
        "salesman_filter": salesman,
        "salesman_filter_name": selected_salesman_name,
    }

    business_insights: list[str] = []
    salesman_top1 = salesman_summary["top1_profit_concentration_pct"]
    salesman_top3 = salesman_summary["top3_profit_concentration_pct"]
    customer_top1 = customer_summary["top1_profit_concentration_pct"]
    customer_top5 = customer_summary["top5_profit_concentration_pct"]
    if salesman_top1 is None:
        business_insights.append("可识别业务员净毛利润分母不大于零，暂不判断业务员集中度。")
    elif salesman_top1 >= 50 or (salesman_top3 or 0) >= 80:
        business_insights.append("品类毛利润集中于少数业务员，广告获客方法是否能跨业务员复制需单独验证。")
    else:
        business_insights.append("业务员毛利润分布相对分散，暂未看到明显的单一业务员依赖。")
    if customer_top1 is None:
        business_insights.append("可识别客户净毛利润分母不大于零，暂不判断客户集中度。")
    elif customer_top1 >= 50:
        business_insights.append("存在明显单一客户依赖，投放判断应先剔除该客户后复核剩余利润空间。")
    elif (customer_top5 or 0) >= 80:
        business_insights.append("品类毛利润集中于少数客户，广告扩大客户面可能有价值，但可复制性仍需小额测试。")
    else:
        business_insights.append("客户毛利润分布相对分散，客户结构对广告测试的限制较小。")
    business_insights.append("以上仅描述现有业务结构，不自动推断 Facebook 广告获客效果。")

    monthly: list[dict[str, Any]] = []
    monthly_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in dimension_orders:
        monthly_groups[order["shipping_date"].strftime("%Y-%m")].append(order)
    category_first_orders = _category_first_orders(history)
    for month, month_orders in sorted(monthly_groups.items()):
        month_ids = {order["id"] for order in month_orders}
        covered_month_orders = [order for order in month_orders if order["gross_profit"] is not None]
        monthly.append({
            "month": month,
            "category": category,
            "order_count": len(month_orders),
            "database_first_customer_count": sum(first["id"] in month_ids for first in first_orders.values()),
            "category_first_customer_count": sum(first["id"] in month_ids for first in category_first_orders.values()),
            "total_profit": _round(_sum_profit(month_orders)),
            "avg_order_profit": _round(_sum_profit(month_orders) / len(covered_month_orders)) if covered_month_orders else None,
        })

    raw_names = Counter(order["product_name"] or UNKNOWN_CATEGORY for order in category_orders)
    return {
        "category": category,
        "metric": metric,
        "monthly": monthly,
        "channels": channels,
        "dimension_scope": {"salesman": salesman, "salesman_name": selected_salesman_name},
        "raw_product_names": [{"name": name, "order_count": count} for name, count in raw_names.most_common(20)],
        "salesman_contribution": {"summary": salesman_summary, "items": salespeople},
        "customer_contribution": {"summary": customer_summary, "items": customers},
        "business_insights": business_insights,
        "contribution_note": (
            "表格贡献占比以当前明细范围可计算净毛利润为分母；TOP集中度仅以可识别归属的净毛利润为分母。"
            "分母不大于零时不计算百分比，负毛利润保留为负贡献。"
        ),
        "disclaimer": analysis["disclaimer"],
    }


def build_order_drilldown(
    raw_rows: Iterable[dict[str, Any]],
    scope: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    channel: Optional[str] = None,
    salesman: Optional[str] = None,
    customer: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return auditable order rows for a summary metric without mutating source data."""
    orders = [prepare_order(dict(row)) for row in raw_rows]
    if not orders:
        return []
    data_end = max(order["shipping_date"] for order in orders)
    end = min(end_date or data_end, data_end)
    start = start_date or end - timedelta(days=179)
    first_orders, _ = _customer_history(orders)
    first_ids = {order["id"] for order in first_orders.values()}

    selected = [order for order in orders if start <= order["shipping_date"] <= end]
    if category:
        selected = [order for order in selected if order["category"] == category]
    if channel:
        selected = [order for order in selected if (order.get("shipping_channel") or "").strip() == channel]
    if salesman:
        salesman_name = None if salesman == UNKNOWN_GROUP_KEY else salesman
        selected = [order for order in selected if ((order.get("salesman") or "").strip() or None) == salesman_name]
    if customer:
        customer_name = None if customer == UNKNOWN_GROUP_KEY else customer
        selected = [order for order in selected if order["shipping_customer"] == customer_name]

    predicates = {
        "all": lambda order: True,
        "profit_covered": lambda order: order["gross_profit"] is not None,
        "missing_cost": lambda order: order["missing_cost"],
        "negative_profit": lambda order: order["gross_profit"] is not None and order["gross_profit"] < 0,
        "unmatched_customer": lambda order: not order["customer_identifiable"],
        "pending_category": lambda order: order["category"] == PENDING_CATEGORY,
        "unknown_category": lambda order: order["category"] == UNKNOWN_CATEGORY,
        "unclassified_category": lambda order: order["category"] in {PENDING_CATEGORY, UNKNOWN_CATEGORY},
        "database_first": lambda order: order["id"] in first_ids,
        "cancellation_or_void": lambda order: bool(re.search(r"取消|作废", f"{order.get('product_name') or ''} {order.get('remark') or ''}", re.I)),
        "refund_or_reversal": lambda order: bool(re.search(r"退款|退费|冲销|冲账", f"{order.get('product_name') or ''} {order.get('remark') or ''}", re.I)),
        "compensation_or_supplement": lambda order: bool(re.search(r"赔付|赔款|补单", f"{order.get('product_name') or ''} {order.get('remark') or ''}", re.I)),
    }
    if scope not in predicates:
        raise ValueError("unsupported drilldown scope")

    result = []
    for order in filter(predicates[scope], selected):
        result.append({
            "id": order["id"],
            "company_tracking_no": order.get("company_tracking_no"),
            "shipping_date": order["shipping_date"].isoformat(),
            "shipping_customer": order.get("shipping_customer"),
            "salesman": (order.get("salesman") or "").strip() or None,
            "product_name": order.get("product_name") or None,
            "category": order["category"],
            "shipping_channel": order.get("shipping_channel"),
            "shipping_fee": _round(order["shipping_fee"]),
            "shipping_cost": None if order["missing_cost"] else _round(order["shipping_cost"]),
            "gross_profit": None if order["gross_profit"] is None else _round(order["gross_profit"]),
            "remark": order.get("remark"),
        })
    return sorted(result, key=lambda item: (item["shipping_date"], item["company_tracking_no"] or "", item["id"]), reverse=True)
