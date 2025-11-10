from fastapi import APIRouter, Depends

from api.login import jwt_auth
from server_mgr.pricing_utils import QuoteRequest, get_pricing_for_web_comm

router = APIRouter(prefix="/inner_query", tags=["分类管理"], dependencies=[Depends(jwt_auth)])


@router.post("/min_pricing")
async def get_best_quotes(data: QuoteRequest):

    if not data.extra_fee_data:
        data.extra_fee_data = {}

    data.extra_fee_data["is_inner"] = True

    return await get_pricing_for_web_comm(data)
