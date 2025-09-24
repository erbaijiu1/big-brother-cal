from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.login import jwt_auth
from api_model.api_district import DistrictOut, DistrictCreate, SubDistrictOut, SubDistrictCreate, SubDistrictUpdate
from db.db_models import District, SubDistrict
from db.sqlalchemy_define import get_db

router = APIRouter(prefix="/districts", tags=["District"], dependencies=[Depends(jwt_auth)])

@router.post("/", response_model=DistrictOut)
def create_district(data: DistrictCreate, db: Session = Depends(get_db)):
    # 输入验证
    if not data.name_cn or not data.name_en:
        raise HTTPException(status_code=400, detail="District name cannot be empty")

    try:
        dist = District(name_cn=data.name_cn, name_en=data.name_en)
        db.add(dist)
        db.flush()           # 得到 dist.id
        for sub in data.subs:
            db.add(SubDistrict(district_id=dist.id, **sub.model_dump()))
        db.commit()
        db.refresh(dist)
        return dist
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create district: {str(e)}")


@router.get("/", response_model=list[DistrictOut])
def list_districts(db: Session = Depends(get_db)):
    districts = db.query(District).all()
    sub_districts = db.query(SubDistrict).all()
    
    # 创建一个字典来快速查找district id对应的sub_districts
    sub_districts_by_district = {}
    for sub in sub_districts:
        if sub.district_id not in sub_districts_by_district:
            sub_districts_by_district[sub.district_id] = []
        sub_districts_by_district[sub.district_id].append(sub)
    
    # 将sub_districts关联到对应的district
    for dist in districts:
        dist.subs = sub_districts_by_district.get(dist.id, [])
    
    return districts


@router.put("/{id}", response_model=DistrictOut)
def update_district(id: int, data: DistrictCreate, db: Session = Depends(get_db)):
    dist = db.get(District, id)
    if not dist:
        raise HTTPException(404)
    dist.name_cn, dist.name_en = data.name_cn, data.name_en
    # 清空再重建子区（简单写法）
    db.query(SubDistrict).filter_by(district_id=id).delete()
    for sub in data.subs:
        db.add(SubDistrict(district_id=id, **sub.model_dump()))
    db.commit()
    db.refresh(dist)
    return dist

@router.delete("/{id}")
def delete_district(id: int, db: Session = Depends(get_db)):
    if not db.get(District, id):
        raise HTTPException(404)
    db.query(District).filter_by(id=id).delete()
    db.commit()
    return {"ok": True}


# --------------------- 子区管理接口 ---------------------

@router.post("/{district_id}/subs", response_model=SubDistrictOut)
def create_subdistrict(district_id: int, data: SubDistrictCreate, db: Session = Depends(get_db)):
    """新增子区"""
    # district_id URL参数优先，确保归属正确
    sub = SubDistrict(district_id=district_id, **data.model_dump(exclude={"district_id"}))
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@router.put("/subs/{id}", response_model=SubDistrictOut)
def update_subdistrict(id: int, data: SubDistrictUpdate, db: Session = Depends(get_db)):
    """编辑子区"""
    sub = db.get(SubDistrict, id)
    if not sub:
        raise HTTPException(404, "SubDistrict not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(sub, key, value)
    db.commit()
    db.refresh(sub)
    return sub

@router.delete("/subs/{id}")
def delete_subdistrict(id: int, db: Session = Depends(get_db)):
    """删除子区"""
    sub = db.get(SubDistrict, id)
    if not sub:
        raise HTTPException(404, "SubDistrict not found")
    db.delete(sub)
    db.commit()
    return {"ok": True}

@router.get("/{district_id}/subs", response_model=list[SubDistrictOut])
def list_subdistricts(district_id: int, db: Session = Depends(get_db)):
    """获取某行政区的所有子区"""
    return db.query(SubDistrict).filter_by(district_id=district_id).all()

@router.get("/subs/{id}", response_model=SubDistrictOut)
def get_subdistrict(id: int, db: Session = Depends(get_db)):
    """获取单个子区"""
    sub = db.get(SubDistrict, id)
    if not sub:
        raise HTTPException(404, "SubDistrict not found")
    return sub

# 可选：切换偏远区（其实直接 update_subdistrict 也可以实现）
@router.put("/subs/{id}/remote", response_model=SubDistrictOut)
def set_subdistrict_remote(id: int, is_remote: bool, db: Session = Depends(get_db)):
    sub = db.get(SubDistrict, id)
    if not sub:
        raise HTTPException(404, "SubDistrict not found")
    sub.is_remote = is_remote
    db.commit()
    db.refresh(sub)
    return sub
