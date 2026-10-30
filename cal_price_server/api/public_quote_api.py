"""Public, read-only lookup APIs required by the customer quote website."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.district_mgr import list_districts
from api_model.api_district import DistrictOut
from db.sqlalchemy_define import get_db


router = APIRouter(prefix="/public", tags=["Public Quote"])


@router.get("/districts", response_model=list[DistrictOut])
def public_districts(db: Session = Depends(get_db)):
    """Return district and sub-district data without exposing admin mutations."""

    return list_districts(db)
