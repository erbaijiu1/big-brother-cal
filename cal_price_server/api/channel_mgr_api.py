from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Literal, Dict, Any, Set
from pydantic import BaseModel, Field, root_validator, validator
from pydantic import model_validator
import json
import time

from api_model.api_request import ChannelQuery
from db.db_models import ChannelConfig, AreaCategory, AreaCategoryMap, District, SubDistrict
from db.sqlalchemy_define import get_db

router = APIRouter(prefix="/channel_mgr", tags=["渠道管理"])

# ==============================
# 一、工具：安全 JSON 解析 / 序列化
# ==============================
def _json_loads_maybe(s: Any) -> Any:
    if s is None:
        return None
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except Exception:
        # 兜底：返回原始字符串，前端自行处理
        return s

def _json_dumps(data: Any) -> str:
    try:
        return json.dumps(data or {}, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return "{}"


# ==============================
# 二、规范化的 Surcharge Schema
# ==============================
class SurchargeConditions(BaseModel):
    # 可扩展：车型、时间段等
    volume_range: Optional[str] = None   # 例 "0-0.2"
    weight_range: Optional[str] = None
    vehicle: Optional[str] = None

class SurchargeScope(BaseModel):
    mode: Literal["area_category", "district", "sub_district"]
    ids: List[int] = Field(default_factory=list)

class SurchargeRule(BaseModel):
    # key: str = Field(..., description="业务唯一键，如 sea_crossing_fee_van")
    title: str = Field(..., description="显示标题")
    type: Literal["global", "area"] = "global"
    price: int = 0
    combine: Literal["sum", "max", "first"] = "sum"
    conditions: Optional[SurchargeConditions] = None

    # 仅当 type=area 时需要
    scope: Optional[SurchargeScope] = None

    # 解析策略：runtime=运行时解析；snapshot=保存时固化子区快照
    resolve: Literal["runtime", "snapshot"] = "runtime"
    sub_ids_snapshot: Optional[List[int]] = None  # snapshot 模式下保存的快照

    @model_validator(mode='after')
    def _check_area_scope(cls, values):
        # t = values.get("type")
        # 修复方案2：如果需要安全访问，使用getattr
        t = getattr(values, 'type', None)
        scope = getattr(values, 'scope', None)
        if t == "area" and not scope:
            raise ValueError("type=area 时必须提供 scope")
        return values

class ChannelSurchargePayload(BaseModel):
    surcharges: List[SurchargeRule] = Field(default_factory=list)


# ==============================
# 三、区域解析 & 简易缓存
# ==============================
class _AreaCache:
    """进程级简易缓存，避免频繁查询映射关系"""
    _ts: float = 0.0
    _area_cat_map: Dict[int, List[int]] = {}      # category_id -> [sub_ids]
    _district_map: Dict[int, List[int]] = {}      # district_id -> [sub_ids]

    @classmethod
    def warmup(cls, db: Session):
        # area_category 映射
        cat_rows = db.query(AreaCategoryMap).all()
        cls._area_cat_map = {}
        for r in cat_rows:
            cls._area_cat_map.setdefault(r.category_id, []).append(r.sub_district_id)

        # district -> sub_district
        dist_rows = db.query(SubDistrict.id, SubDistrict.district_id).all()
        cls._district_map = {}
        for sid, did in dist_rows:
            cls._district_map.setdefault(did, []).append(sid)

        cls._ts = time.time()

    @classmethod
    def clear(cls):
        cls._ts = 0.0
        cls._area_cat_map = {}
        cls._district_map = {}

def _resolve_scope_to_sub_ids(db: Session, scope: SurchargeScope) -> List[int]:
    # 懒加载缓存
    if _AreaCache._ts == 0.0:
        _AreaCache.warmup(db)

    if scope.mode == "area_category":
        sub_ids: Set[int] = set()
        for cid in scope.ids:
            for sid in _AreaCache._area_cat_map.get(cid, []):
                sub_ids.add(sid)
        return sorted(sub_ids)

    elif scope.mode == "district":
        sub_ids: Set[int] = set()
        for did in scope.ids:
            for sid in _AreaCache._district_map.get(did, []):
                sub_ids.add(sid)
        return sorted(sub_ids)

    elif scope.mode == "sub_district":
        # 直接就是子区 id
        return sorted(set(scope.ids or []))

    else:
        return []


# ==============================
# 四、你原有的接口（小幅增强：解析 JSON 返回）
# ==============================
@router.post("/")
def list_channel(query: ChannelQuery, db: Session = Depends(get_db)):
    q = db.query(ChannelConfig)
    if not query.include_deleted:
        q = q.filter(ChannelConfig.delete_flag == 0)

    if query.keyword:
        like = f"%{query.keyword}%"
        q = q.filter(
            (ChannelConfig.channel_code.like(like)) |
            (ChannelConfig.channel_name.like(like))
        )

    total = q.count()
    items = (
        q.order_by(ChannelConfig.id.desc())
         .offset((query.page - 1) * query.page_size)
         .limit(query.page_size)
         .all()
    )

    def serialize(obj: ChannelConfig):
        return {
            "id": obj.id,
            "channel_code": obj.channel_code,
            "channel_name": obj.channel_name,
            "surcharge_rules": _json_loads_maybe(obj.surcharge_rules),  # ✅ 自动解析
            "filter_rules": _json_loads_maybe(obj.filter_rules),        # ✅ 自动解析
            "remark": obj.remark,
            "delete_flag": obj.delete_flag
        }

    return {"data": [serialize(x) for x in items], "total": total}


@router.get("/{id}", summary="渠道详情")
def get_channel(id: int, db: Session = Depends(get_db)):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")
    # ✅ 返回时也自动解析 JSON
    return {
        "id": obj.id,
        "channel_code": obj.channel_code,
        "channel_name": obj.channel_name,
        "surcharge_rules": _json_loads_maybe(obj.surcharge_rules),
        "filter_rules": _json_loads_maybe(obj.filter_rules),
        "remark": obj.remark,
        "delete_flag": obj.delete_flag
    }


@router.post("/add", summary="新增渠道")
def create_channel(data: dict, db: Session = Depends(get_db)):
    obj = ChannelConfig(
        channel_code=data.get("channel_code"),
        channel_name=data.get("channel_name"),
        surcharge_rules=_json_dumps(data.get("surcharge_rules")),
        filter_rules=_json_dumps(data.get("filter_rules")),
        remark=data.get("remark", "")
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id}


@router.put("/{id}", summary="编辑渠道（基础字段+整块 JSON）")
def update_channel(id: int, data: dict, db: Session = Depends(get_db)):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")

    obj.channel_code = data.get("channel_code")
    obj.channel_name = data.get("channel_name")
    obj.surcharge_rules = _json_dumps(data.get("surcharge_rules"))
    obj.filter_rules = _json_dumps(data.get("filter_rules"))
    obj.remark = data.get("remark", "")
    db.commit()
    return {"msg": "ok"}


@router.delete("/{id}", summary="删除渠道")
def delete_channel(id: int, db: Session = Depends(get_db)):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")
    obj.delete_flag = 1
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


# ==============================
# 五、附加费管理专用接口（新增）
# ==============================

@router.get("/{id}/surcharges", summary="获取渠道的附加费（规范化结构）")
def get_channel_surcharges(id: int, db: Session = Depends(get_db)) -> ChannelSurchargePayload:
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")

    data = _json_loads_maybe(obj.surcharge_rules) or {}
    # 允许老数据是 { "surcharges": [...] } 或直接 list
    if isinstance(data, list):
        payload = ChannelSurchargePayload(surcharges=[SurchargeRule(**x) for x in data])
    else:
        payload = ChannelSurchargePayload(**data)
    return payload


@router.put("/{id}/surcharges", summary="保存附加费（校验 + 可选快照解析）")
def save_channel_surcharges(
    id: int,
    payload: ChannelSurchargePayload,
    db: Session = Depends(get_db)
):
    obj = db.query(ChannelConfig).filter(ChannelConfig.id == id).first()
    if not obj:
        raise HTTPException(404, "渠道不存在")

    # 对每条规则做“snapshot”固化（如选择了 snapshot 策略）
    finalized_rules: List[Dict[str, Any]] = []
    for rule in payload.surcharges:
        rule_dict = rule.dict()
        if rule.type == "area":
            if rule.resolve == "snapshot":
                sub_ids = _resolve_scope_to_sub_ids(db, rule.scope) if rule.scope else []
                rule_dict["sub_ids_snapshot"] = sub_ids
            # runtime 模式不改动，运行时解析
        finalized_rules.append(rule_dict)

    obj.surcharge_rules = _json_dumps({"surcharges": finalized_rules})
    db.commit()
    return {"msg": "ok"}


# ==============================
# 六、（可选）缓存刷新入口
# 调用时机：你在 行政区/类别 发生变更后可触发
# ==============================
@router.post("/_internal/refresh_area_cache", summary="[内部] 刷新区域缓存")
def refresh_area_cache(db: Session = Depends(get_db)):
    _AreaCache.clear()
    _AreaCache.warmup(db)
    return {"msg": "area cache warmed"}
