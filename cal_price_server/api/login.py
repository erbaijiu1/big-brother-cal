from urllib.request import Request

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from starlette import status

from api_model.api_request import LoginForm
from db.db_models import AdminUser
from db.sqlalchemy_define import get_db
from main import app
from server_mgr.jwt_helper import create_access_token, verify_access_token
from passlib.hash import bcrypt



@app.post("/admin/login")
def login(form: LoginForm, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(
        AdminUser.username == form.username,
        AdminUser.status == 1
    ).first()
    if not user or not bcrypt.verify(form.password, user.password):
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
    return payload  # 可返回payload给后续接口用


