from fastapi import HTTPException, Depends, APIRouter, Request
from sqlalchemy.orm import Session
from starlette import status

from api_model.api_request import LoginForm
from db.db_models import AdminUser
from db.sqlalchemy_define import get_db
from server_mgr.jwt_helper import create_access_token, verify_access_token
from passlib.hash import bcrypt

router = APIRouter(prefix="/login", tags=["登录管理"])

# 预计算的 dummy hash，用于统一响应时间
DUMMY_HASH = bcrypt.hash("dummy_password")


@router.post("/admin")
async def login(form: LoginForm, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(
        AdminUser.username == form.username,
        AdminUser.status == 1
    ).first()

    # 统一错误处理，防止账号枚举
    if not user:
        # 使用预计算的 dummy hash 验证以保持响应时间一致
        try:
            bcrypt.verify(form.password, DUMMY_HASH)
        except Exception:
            pass  # 忽略验证结果
        raise HTTPException(401, "账号或密码错误")

    try:
        password_valid = bcrypt.verify(form.password, user.password)
    except (ValueError, bcrypt.exc.InvalidHashError):  # 更具体的异常捕获
        raise HTTPException(401, "账号或密码错误")

    if not password_valid:
        raise HTTPException(401, "账号或密码错误")

    token = create_access_token({"sub": user.username, "uid": user.id})
    return {"token": token, "nickname": user.nickname}


# ---- JWT依赖 ----
def jwt_auth(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")

    token = auth[7:]
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录状态失效，请重新登录")

    # 校验必要字段
    if "sub" not in payload or "uid" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "无效的登录凭证")

    return payload  # 可返回payload给后续接口用
