import urllib.parse
from utils.logger_config import logger

from fastapi import APIRouter, Form, Request

router = APIRouter()

@router.post("/info_upload")
async def receive_contact(request: Request, name: str = Form(...), replyto: str = Form(...), message: str = Form(...)):
    logger.info(f"Received contact info: {name}, {replyto}, {message}")
    return {"success": True, "msg": "已接收"}