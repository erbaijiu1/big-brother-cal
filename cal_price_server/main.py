from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from api.goods_classify import router as classify_router
from api.pricing_rule_api import router as pricing_rule_router
import logging

app = FastAPI()

app.include_router(classify_router, prefix="/cal_prize/classify")
app.include_router(pricing_rule_router, prefix="/cal_prize/pricing_rule")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置简单的日志记录
logging.basicConfig(level=logging.INFO)

# 422异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        # 获取请求的body
        body = await request.body()
        # 打印请求参数和错误信息
        logging.error(f"422 Validation Error! Path: {request.url.path}")
        logging.error(f"Request body: {body.decode('utf-8')}")
        logging.error(f"Validation details: {exc.errors()}")
    except Exception as e:
        logging.error(f"Failed to log request body: {e}")

    # 自定义返回内容
    return JSONResponse(
        status_code=422,
        content={
            "error_code": 422,
            "message": "Validation Error",
            "details": exc.errors()
        },
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.status_code,
            "message": exc.detail,
        },
    )

@app.get("/")
async def root():
    return {"message": "Hello World"}
