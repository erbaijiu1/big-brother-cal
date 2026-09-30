from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.login import jwt_auth
from db.db_models import CooperationQuoteConfig, GoodsClassification, GoodsPriceTierHistory
from db.sqlalchemy_define import get_db
from typing import Optional
from datetime import datetime
import json

from server_mgr.customer_quote_utils import parse_customer_price_tiers

router = APIRouter(prefix="/classify_mgr", tags=["分类管理"], dependencies=[Depends(jwt_auth)])


def _serialize(obj: GoodsClassification) -> dict:
    return {
        "category_id": obj.category_id,
        "main_category": obj.main_category,
        "sub_examples": obj.sub_examples,
        "description": obj.description,
        "temperature_req": obj.temperature_req,
        "hazard_level": obj.hazard_level,
        "storage_level": obj.storage_level,
        "create_time": str(obj.create_time),
        "last_modified": str(obj.last_modified),
        "status": obj.status,
        "priority": obj.priority,
        "customer_price_tiers": parse_customer_price_tiers(obj.customer_price_tiers),
        "price_tiers_updated_at": (
            obj.price_tiers_updated_at.isoformat() if obj.price_tiers_updated_at else None
        ),
        "warehouse_acceptance_policy": obj.warehouse_acceptance_policy,
        "acceptance_notice": obj.acceptance_notice or "",
    }


def _save_tier_history(db: Session, obj: GoodsClassification, tiers: list, auth_payload: dict) -> None:
    db.add(
        GoodsPriceTierHistory(
            category_id=obj.category_id,
            main_category=obj.main_category,
            config_snapshot=json.dumps(tiers, ensure_ascii=False),
            changed_by_id=auth_payload.get("uid"),
            changed_by_name=auth_payload.get("sub"),
        )
    )


def _serialize_cooperation_config(config: CooperationQuoteConfig) -> dict:
    return {
        "category_id": config.category_id,
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
        "config_updated_at": config.config_updated_at.isoformat() if config.config_updated_at else None,
    }

@router.get("/", summary="分类分页列表")
def list_goods(
    page: int = 1,
    page_size: int = 50,
    keyword: Optional[str] = None,
    include_deleted: int = 0,  # 0:只查未删 1:查全部
    db: Session = Depends(get_db)
):
    q = db.query(GoodsClassification)
    if not include_deleted:
        q = q.filter(GoodsClassification.status != 2)  # 只查未删除
    if keyword:
        q = q.filter(GoodsClassification.main_category.like(f"%{keyword}%"))
    total = q.count()
    items = q.order_by(GoodsClassification.priority, GoodsClassification.category_id.desc()).offset((page-1)*page_size).limit(page_size).all()

    return {"data": [_serialize(x) for x in items], "total": total}

@router.get("/{id}", summary="分类详情")
def get_goods(id: int, db: Session = Depends(get_db)):
    obj = db.query(GoodsClassification).filter(GoodsClassification.category_id == id).first()
    if not obj:
        raise HTTPException(404, "分类不存在")
    return _serialize(obj)

@router.post("/", summary="新增分类")
def create_goods(
    data: dict,
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(jwt_auth),
):
    tiers = parse_customer_price_tiers(data.get("customer_price_tiers"))
    policy = data.get("warehouse_acceptance_policy", "MANUAL_CONFIRM")
    if policy not in {"AUTO_ACCEPT", "MANUAL_CONFIRM", "REJECTED"}:
        raise HTTPException(400, "无效的入仓策略")
    obj = GoodsClassification(
        main_category=data.get("main_category"),
        sub_examples=data.get("sub_examples"),
        description=data.get("description"),
        temperature_req=data.get("temperature_req"),
        hazard_level=data.get("hazard_level"),
        storage_level=data.get("storage_level"),
        status=data.get("status", 1),  # 默认正常
        priority=data.get("priority", 99),
        customer_price_tiers=json.dumps(tiers, ensure_ascii=False),
        price_tiers_updated_at=datetime.utcnow(),
        warehouse_acceptance_policy=policy,
        acceptance_notice=data.get("acceptance_notice", ""),
    )
    db.add(obj)
    db.flush()
    _save_tier_history(db, obj, tiers, auth_payload)
    db.commit()
    db.refresh(obj)
    return {"category_id": obj.category_id}

@router.put("/{id}", summary="编辑分类")
def update_goods(
    id: int,
    data: dict,
    db: Session = Depends(get_db),
    auth_payload: dict = Depends(jwt_auth),
):
    obj = db.query(GoodsClassification).filter(GoodsClassification.category_id == id).first()
    if not obj:
        raise HTTPException(404, "分类不存在")
    obj.main_category = data.get("main_category")
    obj.sub_examples = data.get("sub_examples")
    obj.description = data.get("description")
    obj.temperature_req = data.get("temperature_req")
    obj.hazard_level = data.get("hazard_level")
    obj.storage_level = data.get("storage_level")
    obj.status = data.get("status", obj.status)
    obj.priority = data.get("priority", obj.priority)
    policy = data.get("warehouse_acceptance_policy", obj.warehouse_acceptance_policy)
    if policy not in {"AUTO_ACCEPT", "MANUAL_CONFIRM", "REJECTED"}:
        raise HTTPException(400, "无效的入仓策略")
    obj.warehouse_acceptance_policy = policy
    obj.acceptance_notice = data.get("acceptance_notice", obj.acceptance_notice or "")
    if "customer_price_tiers" in data:
        old_tiers = parse_customer_price_tiers(obj.customer_price_tiers)
        new_tiers = parse_customer_price_tiers(data.get("customer_price_tiers"))
        if new_tiers != old_tiers:
            obj.customer_price_tiers = json.dumps(new_tiers, ensure_ascii=False)
            obj.price_tiers_updated_at = datetime.utcnow()
            _save_tier_history(db, obj, new_tiers, auth_payload)
    db.commit()
    return {"msg": "ok"}


@router.get("/{id}/price-tier-history", summary="查询分类对客阶梯价历史")
def get_price_tier_history(id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(GoodsPriceTierHistory)
        .filter(GoodsPriceTierHistory.category_id == id)
        .order_by(GoodsPriceTierHistory.id.desc())
        .limit(100)
        .all()
    )
    return {
        "data": [
            {
                "id": row.id,
                "category_id": row.category_id,
                "main_category": row.main_category,
                "config_snapshot": parse_customer_price_tiers(row.config_snapshot),
                "changed_by_id": row.changed_by_id,
                "changed_by_name": row.changed_by_name,
                "changed_at": row.changed_at.isoformat() if row.changed_at else None,
            }
            for row in rows
        ]
    }


@router.get("/{id}/cooperation-quote", summary="查询品类合作报价配置")
def get_cooperation_quote(id: int, db: Session = Depends(get_db)):
    config = db.query(CooperationQuoteConfig).filter(
        CooperationQuoteConfig.category_id == id
    ).first()
    if not config:
        raise HTTPException(404, "该分类尚未配置合作报价")
    return _serialize_cooperation_config(config)


@router.put("/{id}/cooperation-quote", summary="新增或修改品类合作报价配置")
def save_cooperation_quote(id: int, data: dict, db: Session = Depends(get_db)):
    category = db.query(GoodsClassification).filter(
        GoodsClassification.category_id == id
    ).first()
    if not category:
        raise HTTPException(404, "分类不存在")
    tiers = parse_customer_price_tiers(data.get("price_tiers"))
    if not tiers:
        raise HTTPException(400, "合作报价至少需要一个阶梯价")
    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise HTTPException(400, "enabled 必须是布尔值")
    numeric_fields = (
        "delivery_base_fee",
        "delivery_included_weight",
        "delivery_excess_rate",
    )
    for field in numeric_fields:
        raw_value = data.get(field)
        if raw_value in (None, ""):
            data[field] = None
            continue
        try:
            data[field] = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, f"{field} 必须是数字") from exc
        if data[field] < 0:
            raise HTTPException(400, f"{field} 不能小于 0")
    config = db.query(CooperationQuoteConfig).filter(
        CooperationQuoteConfig.category_id == id
    ).first()
    if not config:
        config = CooperationQuoteConfig(category_id=id, price_tiers="[]")
        db.add(config)
    config.enabled = enabled
    config.currency = data.get("currency") or "CNY"
    config.price_tiers = json.dumps(tiers, ensure_ascii=False)
    for field in (
        "delivery_base_fee",
        "delivery_included_weight",
        "delivery_excess_rate",
        "sea_crossing_notice",
        "upstairs_notice",
        "cutoff_text",
        "eta_text",
        "customer_notice",
    ):
        if field in data:
            setattr(config, field, data[field])
    config.config_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return _serialize_cooperation_config(config)

@router.delete("/{id}", summary="删除分类（软删）")
def delete_goods(id: int, db: Session = Depends(get_db)):
    obj = db.query(GoodsClassification).filter(GoodsClassification.category_id == id).first()
    if not obj:
        raise HTTPException(404, "分类不存在")
    obj.status = 2  # 2=已删除（软删除）
    db.commit()
    return {"msg": "deleted"}

@router.post("/recover/{id}", summary="恢复分类")
def recover_goods(id: int, db: Session = Depends(get_db)):
    obj = db.query(GoodsClassification).filter(GoodsClassification.category_id == id).first()
    if not obj:
        raise HTTPException(404, "分类不存在")
    if obj.status != 2:
        return {"msg": "该分类未被删除，无需恢复"}
    obj.status = 1  # 恢复为正常
    db.commit()
    return {"msg": "已恢复该分类"}
