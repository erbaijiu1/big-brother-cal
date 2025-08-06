from passlib.handlers.bcrypt import bcrypt

from db.db_models import AdminUser
from db.sqlalchemy_define import get_session_factory

Session = get_session_factory()
try:
    with Session() as session:
        hashed = bcrypt.hash("big@123#")

        user = AdminUser(username="big_admin", password=hashed, nickname="超级管理员")
        session.add( user)
        session.commit()
except Exception as e:
    print("finish.")
    raise