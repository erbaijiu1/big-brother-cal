from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api_model.api_request import ChannelQuery
from db.db_models import ChannelConfig
from db.sqlalchemy_define import get_db
from typing import List, Optional
import json

router = APIRouter(prefix="/channel_mgr", tags=["渠道管理"])

@router.post("/")
def list_channel(query: ChannelQuery, db: Session = Depends(get_db)):
    q = db.query(ChannelConfig)

    # ✅ 默认不包含软删项
    if not query.include_deleted:
        q = q.filter(ChannelConfig.delete_flag == 0)

    if query.keyword:
        q = q.filter(ChannelConfig.channel_code.like(f"%{query.keyword}%"))

    total = q.count()
    items = q.order_by(ChannelConfig.id.desc()).offset((query.page-1)*query.page_size).limit(query.page_size).all()

    def serialize(obj):
        return {
            "id": obj.id,
            "channel_code": obj.channel_code,
            "channel_name": obj.channel_name,
            "surcharge_rules": obj.surcharge_rules,
            "filter_rules": obj.filter_rules,
            "remark": obj.remark,
            "delete_flag": obj.delete_flag  # ✅ 返回给前端
        }

    return {"data": [serialize(x) for x in items], "total": total}


@router.get("/{id}", summary="渠道详情")
def get_channel(id: int, db: Session = Depends(get_db)):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")
    return obj

@router.post("/add", summary="新增渠道")
def create_channel(data: dict, db: Session = Depends(get_db)):
    obj = ChannelConfig(
        channel_code=data.get("channel_code"),
        channel_name=data.get("channel_name"),
        surcharge_rules=json.dumps(data.get("surcharge_rules", {}), ensure_ascii=False),
        filter_rules=json.dumps(data.get("filter_rules", {}), ensure_ascii=False),
        remark=data.get("remark", "")
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id}

@router.put("/{id}", summary="编辑渠道")
def update_channel(id: int, data: dict, db: Session = Depends(get_db)):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")
    obj.channel_code = data.get("channel_code")
    obj.channel_name = data.get("channel_name")
    obj.surcharge_rules = json.dumps(data.get("surcharge_rules", {}), ensure_ascii=False)
    obj.filter_rules = json.dumps(data.get("filter_rules", {}), ensure_ascii=False)
    obj.remark = data.get("remark", "")
    db.commit()
    return {"msg": "ok"}


@router.delete("/{id}", summary="删除渠道")
def delete_channel(id: int, db: Session = Depends(get_db)):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")

    obj.delete_flag = 1  # 软删除
    db.commit()

    return {"msg": "渠道已标记为删除"}


@router.post("/recover/{id}", summary="恢复已删除的渠道")
def recover_channel(id: int, db: Session = Depends(get_db)):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")
    if obj.delete_flag == 0:
        return {"msg": "该渠道未被删除，无需恢复"}

    obj.delete_flag = 0
    db.commit()
    return {"msg": "已恢复该渠道"}
