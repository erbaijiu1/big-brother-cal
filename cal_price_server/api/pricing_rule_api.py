from fastapi import APIRouter, HTTPException
from db.pricing_rule_db_handle import get_pricing_rule_by_category_id
from server_mgr.pricing_utils import QuoteRequest, calculate_total_price
from utils.logger_config import logger

router = APIRouter()


@router.post("/min_pricing")
async def get_best_quotes(data: QuoteRequest):
    category_id = data.category_id
    weight = data.weight
    volume = data.volume
    extra_fee_data = data.extra_fee_data

    try:
        rules = get_pricing_rule_by_category_id( category_id)
        quote_list = []

        for rule in rules:
            total_price = calculate_total_price(rule, weight, volume, extra_fee_data)
            quote_list.append({
                "channel": rule.channel,
                "transport_method": rule.transport_method,
                "warehouse": rule.warehouse,
                "total_price": round(total_price, 2),
                "rule_id": rule.id
            })

        sorted_quotes = sorted(quote_list, key=lambda x: x['total_price'])
        return {"code": 200, "message": "success", "data": sorted_quotes}

    except Exception as e:
        logger.error(f"Failed to fetch quote list: {e}")
        raise HTTPException(status_code=500, detail=str(e))
