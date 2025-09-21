from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.login import jwt_auth
from api_model.api_request import PricingRuleCreate
from db.db_models import PricingRule, ChannelConfig, GoodsClassification
from db.sqlalchemy_define import get_db
from typing import Optional
import json

router = APIRouter(prefix="/pricing_mgr", tags=["计费规则管理"])
# router = APIRouter(prefix="/pricing_mgr", tags=["计费规则管理"]
#                    , dependencies=[Depends(jwt_auth)])

@router.get("/", summary="计费规则分页列表")
async def list_pricing(
    page: int = 1, page_size: int = 20,
    channel: Optional[str] = None,
    category_id: Optional[int] = None,
    include_deleted: int = 0,
    db: Session = Depends(get_db)
):
    q = db.query(PricingRule)
    if not include_deleted:
        q = q.filter(PricingRule.status != 2)  # 只查未删除
    if channel:
        q = q.filter(PricingRule.channel == channel)
    if category_id:
        q = q.filter(PricingRule.category_id == category_id)
    total = q.count()
    items = q.order_by(PricingRule.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    def serialize(obj):
        return {
            "id": obj.id,
            "category_id": obj.category_id,
            "channel": obj.channel,
            "transport_method": obj.transport_method,
            "warehouse": obj.warehouse,
            "min_consumption": obj.min_consumption,
            "unit_price_rules": obj.unit_price_rules,
            "discount_price": obj.discount_price,
            "surcharge_fee_rules": obj.surcharge_fee_rules,
            "delivery_fee_rules": obj.delivery_fee_rules,
            "delivery_time": obj.delivery_time,
            "packaging_requirement": obj.packaging_requirement,
            "remark": obj.remark,
            "compensation_policy": obj.compensation_policy,
            "status": obj.status,
            "filter_rules": obj.filter_rules
        }
    return {"data": [serialize(x) for x in items], "total": total}

@router.get("/{id}", summary="计费规则详情")
def get_pricing(id: int, db: Session = Depends(get_db)):
    obj = db.query(PricingRule).filter(PricingRule.id == id).first()
    if not obj:
        raise HTTPException(404, "计费规则不存在")
    return obj

@router.post("/", summary="新增计费规则")
def create_pricing(model: PricingRuleCreate, db: Session = Depends(get_db)):
    # 校验 channel_code
    if not db.query(ChannelConfig).filter(ChannelConfig.channel_code == model.channel).first():
        raise HTTPException(400, f"渠道编码 {model.channel} 不存在")
    # 校验 category_id
    if not db.query(GoodsClassification).filter(GoodsClassification.category_id == model.category_id).first():
        raise HTTPException(400, f"商品分类ID {model.category_id} 不存在")

    obj = PricingRule(
        category_id=model.category_id,
        channel=model.channel,
        transport_method=model.transport_method,
        warehouse=model.warehouse,
        min_consumption=model.min_consumption,
        unit_price_rules=json.dumps(model.unit_price_rules, ensure_ascii=False),
        discount_price=model.discount_price,
        surcharge_fee_rules=json.dumps(model.surcharge_fee_rules, ensure_ascii=False),
        delivery_fee_rules=json.dumps(model.delivery_fee_rules, ensure_ascii=False),
        delivery_time=model.delivery_time,
        packaging_requirement=model.packaging_requirement,
        remark=model.remark,
        compensation_policy=model.compensation_policy,
        status=model.status,
        filter_rules=json.dumps(model.filter_rules, ensure_ascii=False)
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id}



@router.delete("/{id}", summary="删除计费规则-软删")
def delete_pricing(id: int, db: Session = Depends(get_db)):
    obj = db.query(PricingRule).filter(PricingRule.id == id).first()
    if not obj:
        raise HTTPException(404, "计费规则不存在")
    obj.status = 2  # 软删除，2=已删除
    db.commit()
    return {"msg": "deleted"}

@router.post("/recover/{id}", summary="恢复计费规则")
def recover_pricing(id: int, db: Session = Depends(get_db)):
    obj = db.query(PricingRule).filter(PricingRule.id == id).first()
    if not obj:
        raise HTTPException(404, "计费规则不存在")
    if obj.status != 2:
        return {"msg": "该计费规则未被删除，无需恢复"}
    obj.status = 1  # 恢复为正常
    db.commit()
    return {"msg": "已恢复该计费规则"}

@router.put("/{id}", summary="更新计费规则")
def update_pricing(id: int, model: PricingRuleCreate, db: Session = Depends(get_db)):
    obj = db.query(PricingRule).filter(PricingRule.id == id).first()
    if not obj:
        raise HTTPException(404, "计费规则不存在")

    # 校验 channel_code
    if not db.query(ChannelConfig).filter(ChannelConfig.channel_code == model.channel).first():
        raise HTTPException(400, f"渠道编码 {model.channel} 不存在")
    # 校验 category_id
    if not db.query(GoodsClassification).filter(GoodsClassification.category_id == model.category_id).first():
        raise HTTPException(400, f"商品分类ID {model.category_id} 不存在")

    # 更新对象属性
    obj.category_id = model.category_id
    obj.channel = model.channel
    obj.transport_method = model.transport_method
    obj.warehouse = model.warehouse
    obj.min_consumption = model.min_consumption
    obj.unit_price_rules = json.dumps(model.unit_price_rules, ensure_ascii=False)
    obj.discount_price = model.discount_price
    obj.surcharge_fee_rules = json.dumps(model.surcharge_fee_rules, ensure_ascii=False)
    obj.delivery_fee_rules = json.dumps(model.delivery_fee_rules, ensure_ascii=False)
    obj.delivery_time = model.delivery_time
    obj.packaging_requirement = model.packaging_requirement
    obj.remark = model.remark
    obj.compensation_policy = model.compensation_policy
    obj.status = model.status
    obj.filter_rules = json.dumps(model.filter_rules, ensure_ascii=False)

    db.commit()
    db.refresh(obj)
    return {"id": obj.id}

