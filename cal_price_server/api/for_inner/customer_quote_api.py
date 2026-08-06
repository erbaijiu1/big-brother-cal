from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.service_auth import customer_quote_service_auth
from db.db_models import ChannelConfig, GoodsClassification, PricingRule
from db.sqlalchemy_define import get_db
from server_mgr.customer_quote_utils import (
    build_customer_fee_summary,
    parse_customer_price_tiers,
    parse_customer_quote_config,
)
from server_mgr.pricing_utils import QuoteRequest, get_pricing_for_web_comm


router = APIRouter(
    prefix="/internal/customer-quotes",
    tags=["内部对客报价"],
    dependencies=[Depends(customer_quote_service_auth)],
)

LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")


@router.post("/calculate")
async def calculate_customer_quote(data: QuoteRequest, db: Session = Depends(get_db)):
    legacy_result = await get_pricing_for_web_comm(data)
    options = []
    category = db.query(GoodsClassification).filter(
        GoodsClassification.category_id == data.category_id
    ).first()
    customer_price_tiers = parse_customer_price_tiers(
        category.customer_price_tiers if category else None
    )
    price_tiers_updated_at = (
        category.price_tiers_updated_at.replace(tzinfo=LOCAL_TIMEZONE).isoformat()
        if category and category.price_tiers_updated_at
        else None
    )

    for quote in legacy_result.get("data", []):
        rule = db.query(PricingRule).filter(PricingRule.id == quote.get("rule_id")).first()
        channel = db.query(ChannelConfig).filter(
            ChannelConfig.channel_code == quote.get("channel"),
            ChannelConfig.delete_flag == 0,
        ).first()
        fee_summary = build_customer_fee_summary(
            quote.get("fee_details") or [],
            quote["total_price"],
            rule.min_consumption if rule else None,
        )
        service_info = parse_customer_quote_config(channel.customer_quote_config if channel else None)
        upstairs = (data.extra_fee_data or {}).get("need_go_upstairs")
        assumptions = []
        if upstairs in (None, "", -1):
            assumptions.append("客户未提供上楼信息，本次按地面交收计算")

        options.append(
            {
                "channel": quote.get("channel"),
                "transport_method": quote.get("transport_method"),
                "warehouse": quote.get("warehouse"),
                "total_price": quote.get("total_price"),
                "rule_id": quote.get("rule_id"),
                **fee_summary,
                "service_info": service_info,
                "assumptions": assumptions,
                "customer_price_tiers": customer_price_tiers,
                "price_tiers_updated_at": price_tiers_updated_at,
                "config_updated_at": (
                    channel.config_updated_at.replace(tzinfo=LOCAL_TIMEZONE).isoformat()
                    if channel and channel.config_updated_at
                    else None
                ),
            }
        )

    return {
        "code": 200,
        "message": "success",
        "data": {
            "quote_id": f"CQ-{uuid4().hex[:16].upper()}",
            "calculated_at": datetime.now(LOCAL_TIMEZONE).isoformat(),
            "currency": "CNY",
            "input_snapshot": data.model_dump(),
            "category_acceptance": {
                "policy": category.warehouse_acceptance_policy if category else "MANUAL_CONFIRM",
                "notice": category.acceptance_notice or "" if category else "分类未配置，需人工确认",
            },
            "options": options,
        },
    }
