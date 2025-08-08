from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from api_model.api_district import AreaCategoryOut, AreaCategoryCreate
from db.db_models import AreaCategory, AreaCategoryMap
from db.sqlalchemy_define import get_db

router = APIRouter(prefix="/area_categories", tags=["AreaCategory"])

# ---------- 类别 CRUD ----------
@router.get("/", response_model=List[AreaCategoryOut])
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(AreaCategory).all()
    # 查询所有 mapping，一次性查
    relations = db.query(AreaCategoryMap).all()
    sub_ids_map = {}
    for r in relations:
        sub_ids_map.setdefault(r.category_id, []).append(r.sub_district_id)
    return [
        AreaCategoryOut(id=c.id, name=c.name, sub_ids=sub_ids_map.get(c.id, []))
        for c in cats
    ]

@router.post("/", response_model=AreaCategoryOut)
def create_category(data: AreaCategoryCreate, db: Session = Depends(get_db)):
    cat = AreaCategory(**data.dict())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return AreaCategoryOut(id=cat.id, name=cat.name, sub_ids=[])

@router.put("/{cat_id}", response_model=AreaCategoryOut)
def update_category(cat_id: int, data: AreaCategoryCreate, db: Session = Depends(get_db)):
    cat = db.get(AreaCategory, cat_id) or _404()
    cat.name = data.name
    db.commit()
    # 查 mapping
    rels = db.query(AreaCategoryMap).filter_by(category_id=cat_id).all()
    sub_ids = [r.sub_district_id for r in rels]
    return AreaCategoryOut(id=cat.id, name=cat.name, sub_ids=sub_ids)

@router.delete("/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    # 级联删除所有 mapping
    db.query(AreaCategoryMap).filter_by(category_id=cat_id).delete()
    db.query(AreaCategory).filter_by(id=cat_id).delete()
    db.commit()
    return {"ok": True}

# ---------- 绑定 / 解绑 子区 ----------
from pydantic import BaseModel

class BindSubsIn(BaseModel):
    sub_ids: List[int]

@router.post("/{cat_id}/subs")
def bind_subs(cat_id: int, bind: BindSubsIn = Body(...), db: Session = Depends(get_db)):
    cat = db.get(AreaCategory, cat_id) or _404()
    # 先删再插，保证同步
    db.query(AreaCategoryMap).filter_by(category_id=cat_id).delete()
    for sub_id in bind.sub_ids:
        db.add(AreaCategoryMap(category_id=cat_id, sub_district_id=sub_id))
    db.commit()
    return {"ok": True}

@router.delete("/{cat_id}/subs/{sub_id}")
def unbind_sub(cat_id: int, sub_id: int, db: Session = Depends(get_db)):
    db.query(AreaCategoryMap).filter_by(
        category_id=cat_id, sub_district_id=sub_id).delete()
    db.commit()
    return {"ok": True}

def _404():
    raise HTTPException(404)
