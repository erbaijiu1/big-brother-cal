from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.db_models import ChannelConfig
from db.sqlalchemy_define import get_db


router = APIRouter(prefix="/inner/channel", tags=["内部渠道查询"])


@router.get("/{channel_code}")
def get_channel_info(channel_code: str, db: Session = Depends(get_db)):
    config = db.query(ChannelConfig).filter(
        ChannelConfig.channel_code == channel_code,
        ChannelConfig.delete_flag == 0,
    ).first()
    if config is None:
        raise HTTPException(status_code=404, detail=f"渠道 {channel_code} 不存在")
    return {
        "code": 200,
        "message": "success",
        "data": {
            "channel_code": config.channel_code,
            "channel_name": config.channel_name,
            "receiving_address": (config.receiving_address or "").strip(),
            "remark": config.remark or "",
        },
    }
