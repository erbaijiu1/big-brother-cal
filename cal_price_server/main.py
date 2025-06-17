from fastapi import FastAPI, HTTPException, Depends, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from api.goods_classify import router as classify_router
from api.pricing_rule_api import router as pricing_rule_router

app = FastAPI()

app.include_router(classify_router, prefix="/cal_prize/classify")
app.include_router(pricing_rule_router, prefix="/cal_prize/pricing_rule")

# add CORS
# allow_origins = ["https://example.com", "http://localhost:3000"],  # 替换为实际允许的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
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


