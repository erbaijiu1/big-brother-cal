from fastapi import APIRouter, HTTPException
from db.pricing_rule_db_handle import get_pricing_rule_by_category_id
from server_mgr.pricing_utils import QuoteRequest, calculate_total_price, check_if_channel_rule_filter
from utils.logger_config import logger

router = APIRouter()


@router.post("/min_pricing")
async def get_best_quotes(data: QuoteRequest):
    category_id = data.category_id
    weight = data.weight
    volume = data.volume
    extra_fee_data = data.extra_fee_data

    try:
        rules = get_pricing_rule_by_category_id(category_id)
        quote_list = []

        for rule in rules:
            try:
                if check_if_channel_rule_filter(rule, extra_fee_data, weight, volume):
                    logger.info(f"Skipping rule, channel: {rule.channel}, rule id:{rule.id}")
                    continue

                total_price, channel_conf, fee_details = calculate_total_price(rule, weight, volume, extra_fee_data)
                if total_price <= 0:
                    continue
                if total_price < rule.min_consumption:
                    total_price = rule.min_consumption

                quote_list.append({
                    "channel": rule.channel,
                    "transport_method": rule.transport_method,
                    "warehouse": rule.warehouse,
                    "total_price": round(total_price, 2),
                    "rule_id": rule.id
                    , "remark": channel_conf.remark if channel_conf else ""
                    , "fee_details": fee_details
                })
                logger.info(f"Quote for channel {rule.channel} is {total_price}")
            except Exception as e:
                logger.error(f"Failed to calculate quote for channel {rule.channel}: {e}", exc_info=True)

        sorted_quotes = sorted(quote_list, key=lambda x: x['total_price'])
        return {"code": 200, "message": "success", "data": sorted_quotes}

    except Exception as e:
        logger.error(f"Failed to fetch quote list: {e}")
        raise HTTPException(status_code=500, detail=str(e))
