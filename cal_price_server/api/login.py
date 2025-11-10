from fastapi import HTTPException, Request
from starlette import status
from server_mgr.jwt_helper import verify_access_token


# ---- JWT依赖 ----
def jwt_auth(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")

    token = auth[7:]
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录状态失效，请重新登录")

    if "sub" not in payload or "uid" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效的登录凭证")

    return payload


def get_user_priority(payload: dict) -> int:
    """
    简单的优先级映射：big_admin=100，其它=1
    （后续可替换为 DB/角色-权限体系）
    """
    return 100 if payload.get("sub") == "big_admin" else 1

