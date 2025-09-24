from fastapi import HTTPException, Depends, APIRouter, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field
from passlib.hash import bcrypt

from db.db_models import AdminUser
from db.sqlalchemy_define import get_db
from api.login import jwt_auth  # 依赖验证

router = APIRouter(prefix="/admin_user", tags=["管理员管理"])

# ==== 状态常量 ====
class UserStatus:
    ENABLED = 1
    DISABLED = 0
    DELETED = 2


# ==== Pydantic 模型 ====
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


# ==== 超级管理员验证依赖 ====
def super_admin_required(payload: dict = Depends(jwt_auth)):
    if payload.get("username") != "big_admin":
        raise HTTPException(403, "只有超级管理员可以访问此接口")
    return payload


# ==== 管理员用户管理 ====
@router.post("/", response_model=AdminUserResponse, summary="创建管理员用户")
def create_admin_user(
    user: AdminUserCreate,
    db: Session = Depends(get_db),
    payload: dict = Depends(super_admin_required)
):
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


@router.get("/", summary="获取管理员用户列表")
def list_admin_users(
    page: int = 1,
    page_size: int = 20,
    username: Optional[str] = None,
    status: Optional[str] = Query(None),  # ★ 接收为 str，更宽容
    db: Session = Depends(get_db),
    payload: dict = Depends(super_admin_required)
):
    query = db.query(AdminUser)

    if username:
        query = query.filter(AdminUser.username.like(f"%{username}%"))

    # 仅当 status 有效数字时才过滤
    if status not in (None, ""):
        try:
            query = query.filter(AdminUser.status == int(status))
        except ValueError:
            # 给个更友好的错误，或直接忽略
            raise HTTPException(422, "status 必须是整数")

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "items": users}

@router.get("/{user_id}", response_model=AdminUserResponse, summary="获取管理员用户详情")
def get_admin_user(user_id: int, db: Session = Depends(get_db), payload: dict = Depends(super_admin_required)):
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return user


@router.put("/{user_id}", response_model=AdminUserResponse, summary="更新管理员用户")
def update_admin_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(get_db),
    payload: dict = Depends(super_admin_required)
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


@router.delete("/{user_id}", summary="删除管理员用户")
def delete_admin_user(user_id: int, db: Session = Depends(get_db), payload: dict = Depends(super_admin_required)):
    db_user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not db_user:
        raise HTTPException(404, "用户不存在")

    db_user.status = UserStatus.DELETED
    db.commit()
    return {"message": "用户已删除"}