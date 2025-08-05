from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.db_models import GoodsClassification
from db.sqlalchemy_define import get_db
from typing import Optional

router = APIRouter(prefix="/classify_mgr", tags=["分类管理"])

@router.get("/", summary="分类分页列表")
def list_goods(
    page: int = 1,
    page_size: int = 20,
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

    def serialize(obj):
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
            "priority": obj.priority
        }
    return {"data": [serialize(x) for x in items], "total": total}

@router.get("/{id}", summary="分类详情")
def get_goods(id: int, db: Session = Depends(get_db)):
    obj = db.query(GoodsClassification).filter(GoodsClassification.category_id == id).first()
    if not obj:
        raise HTTPException(404, "分类不存在")
    return obj

@router.post("/", summary="新增分类")
def create_goods(data: dict, db: Session = Depends(get_db)):
    obj = GoodsClassification(
        main_category=data.get("main_category"),
        sub_examples=data.get("sub_examples"),
        description=data.get("description"),
        temperature_req=data.get("temperature_req"),
        hazard_level=data.get("hazard_level"),
        storage_level=data.get("storage_level"),
        status=data.get("status", 1),  # 默认正常
        priority=data.get("priority", 99)
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"category_id": obj.category_id}

@router.put("/{id}", summary="编辑分类")
def update_goods(id: int, data: dict, db: Session = Depends(get_db)):
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
    db.commit()
    return {"msg": "ok"}

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
