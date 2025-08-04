from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.db_models import PricingRule
from db.sqlalchemy_define import get_db
from typing import Optional
import json

router = APIRouter(prefix="/admin/pricing", tags=["计费规则管理"])

@router.get("/", summary="计费规则分页列表")
def list_pricing(page: int = 1, page_size: int = 20, channel: Optional[str] = None, category_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(PricingRule)
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
def create_pricing(data: dict, db: Session = Depends(get_db)):
    obj = PricingRule(
        category_id=data.get("category_id"),
        channel=data.get("channel"),
        transport_method=data.get("transport_method"),
        warehouse=data.get("warehouse"),
        min_consumption=data.get("min_consumption"),
        unit_price_rules=json.dumps(data.get("unit_price_rules", []), ensure_ascii=False),
        discount_price=data.get("discount_price", ""),
        surcharge_fee_rules=json.dumps(data.get("surcharge_fee_rules", []), ensure_ascii=False),
        delivery_fee_rules=json.dumps(data.get("delivery_fee_rules", []), ensure_ascii=False),
        delivery_time=data.get("delivery_time", ""),
        packaging_requirement=data.get("packaging_requirement", ""),
        remark=data.get("remark", ""),
        compensation_policy=data.get("compensation_policy", ""),
        status=data.get("status", 1),
        filter_rules=json.dumps(data.get("filter_rules", []), ensure_ascii=False)
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id}

@router.put("/{id}", summary="编辑计费规则")
def update_pricing(id: int, data: dict, db: Session = Depends(get_db)):
    obj = db.query(PricingRule).filter(PricingRule.id == id).first()
    if not obj:
        raise HTTPException(404, "计费规则不存在")
    obj.category_id = data.get("category_id")
    obj.channel = data.get("channel")
    obj.transport_method = data.get("transport_method")
    obj.warehouse = data.get("warehouse")
    obj.min_consumption = data.get("min_consumption")
    obj.unit_price_rules = json.dumps(data.get("unit_price_rules", []), ensure_ascii=False)
    obj.discount_price = data.get("discount_price", "")
    obj.surcharge_fee_rules = json.dumps(data.get("surcharge_fee_rules", []), ensure_ascii=False)
    obj.delivery_fee_rules = json.dumps(data.get("delivery_fee_rules", []), ensure_ascii=False)
    obj.delivery_time = data.get("delivery_time", "")
    obj.packaging_requirement = data.get("packaging_requirement", "")
    obj.remark = data.get("remark", "")
    obj.compensation_policy = data.get("compensation_policy", "")
    obj.status = data.get("status", 1)
    obj.filter_rules = json.dumps(data.get("filter_rules", []), ensure_ascii=False)
    db.commit()
    return {"msg": "ok"}

@router.delete("/{id}", summary="删除计费规则")
def delete_pricing(id: int, db: Session = Depends(get_db)):
    obj = db.query(PricingRule).filter(PricingRule.id == id).first()
    if not obj:
        raise HTTPException(404, "计费规则不存在")
    db.delete(obj)
    db.commit()
    return {"msg": "deleted"}
