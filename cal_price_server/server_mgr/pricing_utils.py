import json
from typing import Optional, Dict, Any, List, Tuple

from pydantic import BaseModel, Field

import config
from db.channel_db_handle import get_channel_config_by_channel
from db.db_models import PricingRule
from utils.logger_config import logger


class QuoteRequest(BaseModel):
    category_id: int = Field(..., description="分类ID")
    weight: float = Field(..., description="重量 KG")
    volume: float = Field(..., description="体积 CBM")
    extra_fee_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="附加上下文参数"
    )


class FeeDetail(BaseModel):
    name: str                      # 费用项名称，如 "unit_price"、"delivery_fee"、"sea_crossing_fee"
    rule: Dict[str, Any]           # 生效的规则原文
    applied_value: float           # 用于匹配规则的值（如 weight 或 volume)
    amount: float                  # 此项费用金额
    cn_name: Optional[ str]        # 中文名称


def parse_range(r: str) -> Tuple[float, float]:
    low, high = r.split('-')
    return float(low), float(high)


def match_range(value: float, r: str) -> bool:
    low, high = parse_range(r)
    return low < value <= high


def calculate_range_fee(value: float, rules: List[Dict[str, Any]]):
    for rule in rules:
        low, high = parse_range(rule['range'])
        if low < value <= high:
            if 'price' in rule:
                return rule['price'], rule
            if 'unit_price' in rule:
                base = rule.get('base_fees', 0)
                v = value - rule.get('deduction_value', 0)
                if v <= 0:
                    v = 0.0
                return round(base + v * rule['unit_price'], 2), rule
    return 0.0, None


def calculate_surcharge_with_breakdown(
    context: Dict[str, Any],
    surcharge_rules: Dict[str, List[Dict[str, Any]]]
) -> List[FeeDetail]:
    """
    对 context 中的 weight, volume, sub_district, destination, elevator 信息进行匹配，
    返回每条命中规则的 FeeDetail 列表（不累加，逐条返回）
    """
    breakdown: List[FeeDetail] = []
    volume = context.get('volume', 0.0)
    weight = context.get('weight', 0.0)

    # 海跨费
    for rule in surcharge_rules.get('sea_crossing_fee', []):
        vmin, vmax = parse_range(rule['volume_range'])
        wmin, wmax = parse_range(rule['weight_range'])
        if vmin < volume <= vmax and wmin < weight <= wmax \
                and context.get("district", 'not_found') in rule.get("district_cn_in", "empty_list"):
            breakdown.append(FeeDetail(
                name='sea_crossing_fee',
                cn_name = '海跨费',
                rule=rule,
                applied_value=max(volume, weight),
                amount=rule['price']
            ))

    # 区域附加费
    for rule in surcharge_rules.get('area_fee', []):
        subs = [s.strip() for s in rule['sub_districts_in'].replace('，', ',').split(',')]
        if context.get('sub_district') in subs:
            breakdown.append(FeeDetail(
                name='area_fee',
                rule=rule,
                applied_value=0.0,
                amount=rule['price'],
                cn_name = '区域附加费'
            ))

    # 远程区附加费（取最高档次）
    max_price = 0.0
    best_rule: Optional[Dict[str, Any]] = None
    for rule in surcharge_rules.get('remote_area_add_fee', []):
        subs = [s.strip() for s in rule['sub_districts_in'].replace('，', ',').split(',')]
        if context.get('sub_district') in subs and rule['price'] > max_price:
            max_price = rule['price']
            best_rule = rule
    if best_rule:
        breakdown.append(FeeDetail(
            name='remote_area_add_fee',
            rule=best_rule,
            applied_value=0.0,
            amount=max_price,
            cn_name='远程区附加费'
        ))

    # 电梯搬运费
    upstairs_cfg = surcharge_rules.get('elevator_handling_fee', {})
    if upstairs_cfg:
        match = True
        for k in ['need_go_upstairs', 'has_elevator', 'need_stairs']:
            if k not in upstairs_cfg:
                continue
            if context.get(k, -1) != upstairs_cfg.get(k, -1):
                match = False
                break
        if match and 'price' in upstairs_cfg:
            breakdown.append(FeeDetail(
                name='elevator_handling_fee',
                rule=upstairs_cfg,
                applied_value=0.0,
                amount=upstairs_cfg['price']
                ,cn_name='上楼费'
            ))

    return breakdown


def get_type_max_fee(price_rules: str, volume: float, weight: float, details: List[FeeDetail], name: str, cn_name: str) -> float:
    if not price_rules or len(price_rules)<=0 :
        return 0.0

    # 1. 单价费用
    unit_rules = json.loads(price_rules)
    kg_unit_rules = [r for r in unit_rules if r['prize_type'] == 'KG']
    cbm_unit_rules = [r for r in unit_rules if r['prize_type'] == 'CBM']
    # 如果没有 CBM 规则，刚CBM转换成KG , 一立方等于200公斤, 向上取整，2位
    if not cbm_unit_rules:
        weight = max(round(volume * 200, 2), weight)

    kg_price, w_unit_rule = calculate_range_fee(weight, kg_unit_rules)
    cbm_price, v_unit_rule = calculate_range_fee(volume, cbm_unit_rules)
    unit_price = max(kg_price, cbm_price)
    target_rule, target_unit = (w_unit_rule, weight) if kg_price >= cbm_price else (v_unit_rule, volume)

    # 增加我们要挣的钱
    if name in config.EXTRA_FEE_ITEMS:
        earn_money = max(config.MIN_EARN_MONEY, unit_price * config.EARN_MONEY_RATIO)
        unit_price = unit_price + earn_money

    # logger.info(f"unit_price: {unit_price}, earn_money: {earn_money}")
    if target_rule is not None:
        details.append(FeeDetail(
            name=name, rule=target_rule, applied_value=target_unit,
            amount=unit_price,
            cn_name=cn_name
        ))

    return unit_price


def calculate_total_price(
    rule: PricingRule,
    weight: float,
    volume: float,
    extra_fee_data: Dict[str, Any]
) -> Tuple[float, Any, List[FeeDetail]]:
    """
    返回 (total_amount, channel_config, details_list)
    details_list 包含 unit_price, delivery_fee 及每项附加费的明细
    """
    details: List[FeeDetail] = []
    try:
        # 1. 单价费用
        unit_price = get_type_max_fee(rule.unit_price_rules, volume, weight, details, 'unit_price', '单价费用')

        # 2. 派送费
        delivery = get_type_max_fee(rule.delivery_fee_rules, volume, weight, details, 'delivery_fee', '派送费')

        # 3. 附加费
        channel_cfg = get_channel_config_by_channel(rule.channel)
        surcharge_raw = json.loads(channel_cfg.surcharge_rules or '{}')
        surcharge_rules = surcharge_raw.get('surcharges', {})
        # sea_crossing_fee etc.
        for fee in calculate_surcharge_with_breakdown({**extra_fee_data,'weight':weight,'volume':volume}, surcharge_rules):
            details.append(fee)

        total = unit_price + delivery + sum(f.amount for f in details if f.name not in ['unit_price','delivery_fee'])
        return total, channel_cfg, details
    except Exception as e:
        logger.error(f"Error in calculate_total_price: rule_id: {rule.id}, error:{e}", exc_info=True)
        return -1, None, []

def check_if_channel_filter(channel: str, context, weight: float, volume: float) -> bool:
    channel_config = get_channel_config_by_channel( channel)
    return check_filter_rule_imp(channel_config.filter_rules, context, weight, volume)

def check_filter_rule_imp(filter_rules:str, context, weight: float, volume: float):
    filter_config = json.loads(filter_rules or '{}')
    # 没有过滤条件，直接返回 True 或 False，看你的业务需求
    if not filter_config:
        return False

    for key, value in filter_config.items():
        # 处理“区在列表里”
        if key == "sub_districts_in":
            if context.get('sub_district') not in value:
                return False

        # 处理“重量区间”
        elif key == "kg_range":
            low, high = parse_range(filter_config['kg_range'])
            if weight < low or weight > high:
                return False
        # 处理“必须是冷链”
        # elif key == "need_cold_chain":
        #     if context.get('need_cold_chain') != value:
        #         return False
        # ... 未来你可以加 elif 来处理其他类型的过滤条件
        # else:
        #     # 未知字段，按需决定，通常默认跳过或认为不通过
        #     # return False  # 如果遇到未知过滤字段就直接失败
        #     pass

    # 所有过滤条件都通过才返回 True
    return True

def check_if_channel_rule_filter(rule: PricingRule, context, weight, volume):
    if check_if_channel_filter(rule.channel, context, weight, volume):
        logger.info(f"Skipping rule {rule.channel} due to filters")
        return True

    return check_filter_rule_imp(rule.filter_rules, context, weight, volume)

