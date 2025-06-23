import json
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from db.channel_db_handle import get_surcharge_config_by_channel
from db.db_models import PricingRule
from utils.logger_config import logger


class QuoteRequest(BaseModel):
    category_id: int = Field(..., description="分类ID")
    weight: float = Field(..., description="重量 KG")
    volume: float = Field(..., description="体积 CBM")
    extra_fee_data : Optional[Dict[str, Any]] = Field(default_factory=dict, description="附加上下文参数")

def parse_range(r):
    start, end = map(float, r.split('-'))
    return start, end

def match_range(v, r):
    start, end = parse_range(r)
    return start < v <= end


def calculate_rule_group(group: list, volume: float, weight: float, destination: str) -> float:
    prices = []
    for rule in group:
        if "volume_range" in rule and "weight_range" in rule:
            if match_range(volume, rule['volume_range']) and match_range(weight, rule['weight_range']):
                prices.append(rule['price'])
        elif "destination_list" in rule:
            if destination in rule['destination_list']:
                prices.append(rule['price'])
    return max(prices) if prices else 0


def calculate_surcharge_total(context, surcharge_rules) -> float:
    context = context or {}
    volume = context.get('volume', 0)
    weight = context.get('weight', 0)
    destination = context.get('destination', '')

    total = 0
    for key, group in surcharge_rules.items():
        total += calculate_rule_group(group, volume, weight, destination)
    return total


def get_total_surcharge(params: dict, config: dict, weight, volume) -> float:
    """
    计算总费用。

    params: {
        "district_cn": str,
        "sub_cn": str,
        "volume": float,
        "weight": float,
        "elevator_required": bool
    }
    config: 您提供的费率 JSON 结构，已解析为 Python dict。
    """
    district = params["district"]
    sub = params["sub_district"]
    vol = volume
    wt = weight
    elev = params["need_go_upstairs"]

    total = 0.0

    for item in config:
        # 1. 过海费
        if "sea_crossing_fee" in item:
            for fee in item["sea_crossing_fee"]:
                districts = [d.strip() for d in fee["district_cn_in"].split(",")]
                vmin, vmax = map(float, fee["volume_range"].split("-"))
                wmin, wmax = map(float, fee["weight_range"].split("-"))
                if district in districts and vmin < vol <= vmax and wmin < wt <= wmax:
                    total += fee["price"]
                    break  # 匹配第一个符合的规则

        # 2. 地区附加费
        if "area_fee" in item:
            for fee in item["area_fee"]:
                subs = [s.strip() for s in fee["sub_districts_in"].replace("，", ",").split(",")]
                if sub in subs:
                    total += fee["price"]
                    break

        # 3. 远程区附加费（多档或取最高档）
        if "remote_area_add_fee" in item:
            max_remote = 0
            for fee in item["remote_area_add_fee"]:
                subs = [s.strip() for s in fee["sub_districts_in"].replace("，", ",").split(",")]
                if sub in subs:
                    # 如果想累加所有档次就用 total += fee["price"]
                    # 这里示例取最高档
                    if fee["price"] > max_remote:
                        max_remote = fee["price"]
            total += max_remote

        # 4. 电梯搬运费
        if elev and elev == '1' and "elevator_handling_fee" in item:
            upstairs_fee_cfg = item["elevator_handling_fee"]
            keys = ["need_go_upstairs", "has_elevator", "need_stairs"]
            unmatch = any(params[key] != upstairs_fee_cfg[key] for key in keys)
            if not unmatch and "price" in upstairs_fee_cfg:
                total += upstairs_fee_cfg["price"]

    return total


def calculate_range_fee(value: float, rules: list) -> float:
    for rule in rules:
        low, high = map(float, rule["range"].split("-"))
        if low < value <= high:
            if "price" in rule:
                return rule["price"]
            elif "unit_price" in rule:
                base = rule.get("base_fees", 0)
                if "deduction_value" in rule:
                    value -= rule["deduction_value"]

                return round(base + value * rule["unit_price"], 2)
    return 0  # 若无匹配规则，默认返回 0（或可改为抛异常）


def calculate_total_price(rule: PricingRule, weight: float, volume: float, extra_fee_data: Dict[str, Any]):
    try:
        unit_rules = json.loads(rule.unit_price_rules)
        delivery_rules = json.loads(rule.delivery_fee_rules or '[]')

        def get_price(rules, key, value):
            for price_rule in rules:
                start, end = map(float, price_rule['range'].split('-'))
                if start < value < end:
                    return price_rule.get('unit_price', 0) * value + price_rule.get('total_prize', 0)
            return 0

        kg_price = get_price([r for r in unit_rules if r['prize_type'] == 'KG'], 'weight', weight)
        cbm_price = get_price([r for r in unit_rules if r['prize_type'] == 'CBM'], 'volume', volume)
        unit_price = max(kg_price, cbm_price)

        #kg_delivery = get_price([r for r in delivery_rules if r['prize_type'] == 'KG'], 'weight', weight)
        #cbm_delivery = get_price([r for r in delivery_rules if r['prize_type'] == 'CBM'], 'volume', volume)
        #delivery_price = max(kg_delivery, cbm_delivery)

        # 使用示例
        weight_fee = calculate_range_fee(weight, [r for r in delivery_rules if r["prize_type"] == "KG"])
        volume_fee = calculate_range_fee(volume, [r for r in delivery_rules if r["prize_type"] == "CBM"])
        # 取较高值作为最终派送费
        delivery_price = max(weight_fee, volume_fee)

        channel_config = get_surcharge_config_by_channel(rule.channel)

        # 获取附加费用
        extra_fee = get_total_surcharge_by_channel(channel_config, extra_fee_data, weight, volume)
        logger.info(f"单价费用：{unit_price},派送费：{delivery_price},附加费用：{extra_fee}")

        total = unit_price + delivery_price + extra_fee
        return total, channel_config
    except Exception as e:
        logger.error(f"Error in price calculation: {e}")
        return float('inf')


def get_total_surcharge_by_channel(channel_config, context, weight, volume) -> float:
    try:
        surcharge_rule = channel_config.surcharge_rules
        if not surcharge_rule:
            return 0

        surcharge_rules = json.loads(surcharge_rule)
        if not surcharge_rules:
            return 0

        if "surcharges" in surcharge_rules:
            surcharge_rules = surcharge_rules["surcharges"]

        return get_total_surcharge(context, surcharge_rules, weight, volume)
        # return calculate_surcharge_total(context, surcharge_rules)


    except Exception as e:
        logger.error(f"Error in surcharge calculation: {e}", exc_info=True)