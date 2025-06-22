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


# 扩展后的 SURCHARGE_TABLES，包含电梯费、抛货费、超长费等
SURCHARGE_TABLES = {
    "sea_crossing_fee": [
        {"volume_range": "0-0.2", "weight_range": "0-40", "price": 30},
        {"volume_range": "0-9999", "weight_range": "0-99999", "price": 50}  # truck fallback
    ],
    "self_pickup_registration_fee": [
        {"volume_range": "0-3", "weight_range": "0-1000", "price": 100},
        {"volume_range": "0-6", "weight_range": "0-2000", "price": 200},
        {"volume_range": "0-9", "weight_range": "0-3000", "price": 300}
    ],
    "remote_area_fee": [
        {"destination_list": ["西贡", "东涌", "赤柱", "龙鼓滩", "半山", "沙头角"], "price": 100},
        {"destination_list": ["愉景湾"], "price": 300}
    ],
    "warehouse_queue_fee": [
        {"price": 200}  # 一律按票加收
    ],
    "oversize_fee": [
        {"length_min": 3, "price": 50},
        {"length_min": 4, "price": 100},
        {"length_min": 5, "price": 150},
        {"length_min": 6, "price": 300},
        {"length_min": 7, "price": 600}
    ],
    "elevator_fee": [
        {"condition_key": "elevator_required", "price": 50}
    ],
    "toss_fee": [
        {"unit": "per_cbm", "price": 100, "min_price": 100}  # 抛货/每方，最低100元
    ]
}

# 可配合 context 传入如：{"length": 4.5, "elevator_required": true, "cbm": 1.2}


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


def calculate_total_price(rule: PricingRule, weight: float, volume: float, extra_fee_data: Dict[str, Any]) -> float:
    try:
        unit_rules = json.loads(rule.unit_price_rules)
        delivery_rules = json.loads(rule.delivery_fee_rules or '[]')

        def get_price(rules, key, value):
            for rule in rules:
                start, end = map(float, rule['range'].split('-'))
                if start <= value < end:
                    return rule.get('unit_price', 0) * value + rule.get('total_prize', 0)
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

        # 获取附加费用
        extra_fee = get_total_surcharge_by_channel(rule.channel, extra_fee_data)
        logger.info(f"单价费用：{unit_price},派送费：{delivery_price},附加费用：{extra_fee}")

        total = unit_price + delivery_price + extra_fee
        return total
    except Exception as e:
        logger.error(f"Error in price calculation: {e}")
        return float('inf')


def get_total_surcharge_by_channel(channel: str, context) -> float:
    try:
        channel_config = get_surcharge_config_by_channel(channel)
        if not channel_config:
            return 0

        surcharge_rule = channel_config.surcharge_rules
        if not surcharge_rule:
            return 0

        print(f"id:{channel_config.id}, surcharge_rule:{surcharge_rule}")

        surcharge_rules = json.loads(surcharge_rule)
        return calculate_surcharge_total(context, surcharge_rules)

    except Exception as e:
        logger.error(f"Error in surcharge calculation: {e}", exc_info=True)