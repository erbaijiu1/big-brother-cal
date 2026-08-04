import hmac

from fastapi import HTTPException, Request, status

from config import CUSTOMER_QUOTE_SERVICE_TOKEN


def customer_quote_service_auth(request: Request) -> str:
    if not CUSTOMER_QUOTE_SERVICE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="对客报价服务令牌尚未配置",
        )
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少服务凭证")
    supplied = authorization[7:]
    if not hmac.compare_digest(supplied, CUSTOMER_QUOTE_SERVICE_TOKEN):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="服务凭证无效")
    return supplied
