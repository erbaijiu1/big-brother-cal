from datetime import datetime
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.service_auth import customer_quote_service_auth
from db.db_models import ChannelConfig, CooperationQuoteConfig, GoodsClassification, PricingRule
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


def _serialize_cooperation_quote(
    config: CooperationQuoteConfig,
    category: GoodsClassification,
) -> dict:
    return {
        "category_id": category.category_id,
        "category_name": category.main_category,
        "enabled": bool(config.enabled),
        "currency": config.currency,
        "price_tiers": parse_customer_price_tiers(config.price_tiers),
        "delivery_base_fee": config.delivery_base_fee,
        "delivery_included_weight": config.delivery_included_weight,
        "delivery_excess_rate": config.delivery_excess_rate,
        "sea_crossing_notice": config.sea_crossing_notice or "",
        "upstairs_notice": config.upstairs_notice or "",
        "cutoff_text": config.cutoff_text or "",
        "eta_text": config.eta_text or "",
        "customer_notice": config.customer_notice or "",
        "acceptance_policy": category.warehouse_acceptance_policy,
        "acceptance_notice": category.acceptance_notice or "",
        "config_updated_at": (
            config.config_updated_at.replace(tzinfo=LOCAL_TIMEZONE).isoformat()
            if config.config_updated_at
            else None
        ),
    }


@router.get("/cooperation")
def list_cooperation_quotes(
    category_ids: str = "",
    db: Session = Depends(get_db),
):
    """按品类返回合作报价卡；未配置的品类不回退到单票阶梯价。"""
    raw_ids = [value.strip() for value in category_ids.split(",") if value.strip()]
    if any(not value.isdigit() for value in raw_ids):
        raise HTTPException(status_code=422, detail="category_ids 必须是逗号分隔的整数")
    requested_ids = {
        int(value) for value in raw_ids
    }
    query = (
        db.query(CooperationQuoteConfig, GoodsClassification)
        .join(
            GoodsClassification,
            GoodsClassification.category_id == CooperationQuoteConfig.category_id,
        )
        .filter(CooperationQuoteConfig.enabled.is_(True))
        .filter(GoodsClassification.status != 2)
    )
    if requested_ids:
        query = query.filter(CooperationQuoteConfig.category_id.in_(requested_ids))
    rows = query.order_by(GoodsClassification.priority, GoodsClassification.category_id).all()
    return {
        "code": 200,
        "message": "success",
        "data": [_serialize_cooperation_quote(config, category) for config, category in rows],
    }


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
