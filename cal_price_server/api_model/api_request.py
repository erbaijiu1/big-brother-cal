from typing import Optional

from pydantic import BaseModel


class ChannelQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    keyword: Optional[str] = None
    include_deleted: Optional[bool] = False  # ✅ 新增字段


