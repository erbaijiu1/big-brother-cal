from fastapi import HTTPException, Depends, APIRouter, Request
from sqlalchemy.orm import Session
from starlette import status
from typing import List, Optional
from pydantic import BaseModel, Field
from passlib.hash import bcrypt
from passlib.exc import InvalidHashError

from api_model.api_request import LoginForm
from db.db_models import AdminUser
from db.sqlalchemy_define import get_db
from server_mgr.jwt_helper import create_access_token, verify_access_token

router = APIRouter(prefix="/login", tags=["登录管理"])

# ---- 状态常量 ----
class UserStatus:
    ENABLED = 1    # 启用
    DISABLED = 0   # 禁用
    DELETED = 2    # 已删除（软删除）

# 预计算的 dummy hash，用于统一响应时间
DUMMY_HASH = bcrypt.hash("dummy_password")

# ---- Pydantic 模型 ----
class AdminUserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=8, description="至少8位密码")
    nickname: str = ""
    status: int = UserStatus.ENABLED

class AdminUserUpdate(BaseModel):
    nickname: Optional[str] = None
    status: Optional[int] = None

class AdminUserResponse(BaseModel):
    id: int
    username: str
    nickname: str
    status: int

    class Config:
        orm_mode = True


# ---- 登录接口 ----
@router.post("/admin")
async def login(form: LoginForm, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(
        AdminUser.username == form.username,
        AdminUser.status == UserStatus.ENABLED
    ).first()

    if not user:
        try:
            bcrypt.verify(form.password, DUMMY_HASH)
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


# ---- 管理员用户管理接口 ----
@router.post("/admin_user/", response_model=AdminUserResponse, summary="创建管理员用户")
def create_admin_user(user: AdminUserCreate, db: Session = Depends(get_db), payload: dict = Depends(jwt_auth)):
    existing_user = db.query(AdminUser).filter(AdminUser.username == user.username).first()
    if existing_user:
        raise HTTPException(400, "用户名已存在")

    hashed_password = bcrypt.hash(user.password)
    db_user = AdminUser(
        username=user.username,
        password=hashed_password,
        nickname=user.nickname,
        status=user.status
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/admin_user/", summary="获取管理员用户列表")
def list_admin_users(
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    status: Optional[int] = None,
    db: Session = Depends(get_db),
    payload: dict = Depends(jwt_auth)
):
    query = db.query(AdminUser)

    if username:
        query = query.filter(AdminUser.username.like(f"%{username}%"))
    if status is not None:
        query = query.filter(AdminUser.status == status)

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": users}


@router.get("/admin_user/{user_id}", response_model=AdminUserResponse, summary="获取管理员用户详情")
def get_admin_user(user_id: int, db: Session = Depends(get_db), payload: dict = Depends(jwt_auth)):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user


@router.put("/admin_user/{user_id}", response_model=AdminUserResponse, summary="更新管理员用户")
def update_admin_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(jwt_auth)
):
    db_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not db_user:
        raise HTTPException(404, "用户不存在")

    if user_update.nickname is not None:
        db_user.nickname = user_update.nickname
    if user_update.status is not None:
        db_user.status = user_update.status

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/admin_user/{user_id}", summary="删除管理员用户")
def delete_admin_user(user_id: int, db: Session = Depends(get_db), payload: dict = Depends(jwt_auth)):
    db_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not db_user:
        raise HTTPException(404, "用户不存在")

    db_user.status = UserStatus.DELETED
    db.commit()
    return {"message": "用户已删除"}
