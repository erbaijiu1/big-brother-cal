# schemas.py
from pydantic import BaseModel
from typing import List, Optional

class SubDistrictBase(BaseModel):
    district_id: int
    name_cn: str
    name_en: str
    is_remote: bool = False

class SubDistrictCreate(SubDistrictBase): pass
class SubDistrictUpdate(BaseModel):
    name_cn: str | None = None
    name_en: str | None = None
    is_remote: bool | None = None

class SubDistrictOut(SubDistrictBase):
    id: int
    class Config:
        orm_mode = True

class DistrictBase(BaseModel):
    name_cn: str
    name_en: str

class DistrictCreate(DistrictBase):
    subs: Optional[List[SubDistrictBase]] = []

class DistrictOut(DistrictBase):
    id: int
    subs: List[SubDistrictOut] = []
    class Config: orm_mode = True


class AreaCategoryBase(BaseModel):
    name: str

class AreaCategoryCreate(AreaCategoryBase):
    pass

class AreaCategoryOut(AreaCategoryBase):
    id: int
    sub_ids: List[int] = []
    class Config:
        orm_mode = True
