from fastapi import APIRouter, Depends
from typing import Dict
from api.login import jwt_auth, get_user_priority
from api_model.api_request import MenuItem

router = APIRouter(prefix="/menu_mgr", tags=["菜单管理"])

# ======== 菜单源（可迁移到 DB）========
BASE_MENUS: Dict[str, MenuItem] = {
    "channel":  MenuItem(title="渠道管理", desc="配置物流渠道",
                         path="/pages/admin/channel/index",      order=10, permission_less=100),
    "classify": MenuItem(title="分类管理", desc="管理货物分类",
                         path="/pages/admin/classify_mgr/index", order=20, permission_less=100),
    "district": MenuItem(title="行政区管理", desc="配置区/子区及偏远标记",
                         path="/pages/admin/district/index",     order=30, permission_less=100),
    "pricing":  MenuItem(title="计价规则", desc="设置运费及附加费规则",
                         path="/pages/admin/pricing_mgr/index",  order=40, permission_less=100),
    "user":     MenuItem(title="用户管理", desc="后台用户账号维护",
                         path="/pages/admin/user_mgr/index",     order=50, permission_less=100),
    "cost":     MenuItem(title="渠道成本价查询", desc="渠道成本价查询",
                         path="/pages/admin/pricing_cal/index",  order=60, permission_less=1),
}


@router.get("/menu_list", response_model=dict)
async def get_menu_list(auth_payload: dict = Depends(jwt_auth)):
    user_priority = get_user_priority(auth_payload)
    # 过滤可见菜单
    visible = [m for m in BASE_MENUS.values() if m.permission_less <= user_priority]
    # 按 order 排序
    visible.sort(key=lambda x: (x.order or 9999))
    # 统一返回结构
    return {"code": 200, "message": "success", "data": visible}
