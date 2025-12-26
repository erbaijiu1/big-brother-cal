from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from passlib.exc import InvalidHashError

from api_model.api_request import LoginForm
from db.db_models import AdminUser
from db.sqlalchemy_define import get_db
from server_mgr.jwt_helper import create_access_token
from utils.logger_config import logger

router = APIRouter(prefix="/auth", tags=["认证管理"])

# 预计算的 dummy hash，用于统一响应时间
DUMMY_HASH = bcrypt.hash("dummy_password")

class UserStatus:
    ENABLED = 1
    DISABLED = 0
    DELETED = 2


@router.post("/login")
async def login(form: LoginForm, db: Session = Depends(get_db)):
    """
    管理员登录，返回 JWT Token
    """
    user = db.query(AdminUser).filter(
        AdminUser.username == form.username,
        AdminUser.status == UserStatus.ENABLED
    ).first()

    if not user:
        logger.error(f"用户名不存在: {form.username}")
        try:
            bcrypt.verify(form.password, DUMMY_HASH)  # 防止时序攻击
        except Exception:
            pass
        raise HTTPException(401, "账号或密码错误")

    try:
        password_valid = bcrypt.verify(form.password, user.password)
    except (ValueError, InvalidHashError):
        raise HTTPException(401, "账号或密码错误")

    if not password_valid:
        raise HTTPException(401, "账号或密码错误")

    token = create_access_token({"sub": user.username, "uid": user.id})
    return {
        "token": token,
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname
    }
