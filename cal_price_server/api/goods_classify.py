import json
from fastapi import APIRouter, Body, HTTPException
from starlette.responses import JSONResponse, StreamingResponse
from db import classify_db_handle

router = APIRouter()

@router.post("/classify_list")
async def get_classify_list(data: dict= Body(...)):
    try:
        classify_list = classify_db_handle.get_classify_list()
        # return JSONResponse(content={"code": 200, "message": "success", "data": classify_list})
        return {"code": 200, "message": "success", "data": classify_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

