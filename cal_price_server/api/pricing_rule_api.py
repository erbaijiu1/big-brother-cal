from fastapi import APIRouter
from server_mgr.pricing_utils import QuoteRequest, \
    get_pricing_for_web_comm

router = APIRouter()


@router.post("/min_pricing")
async def get_best_quotes(data: QuoteRequest):

    return await get_pricing_for_web_comm(data)
