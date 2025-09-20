from typing import Optional, Any, List

from pydantic import BaseModel, Field


class ChannelQuery(BaseModel):
    page: int = 1
    page_size: int = 50
    keyword: Optional[str] = None
    include_deleted: Optional[bool] = False  # ✅ 新增字段


class PricingRuleBase(BaseModel):
    category_id: int = Field(..., description="商品分类ID")
    channel: str = Field(..., description="渠道编码")
    transport_method: Optional[str] = Field(None, description="运输方式")
    warehouse: Optional[str] = Field(None, description="仓库")
    min_consumption: Optional[float] = Field(None, description="最低消费")
    unit_price_rules: Any = Field(default_factory=list, description="单位价规则（JSON数组）")
    discount_price: Optional[str] = Field("", description="优惠价")
    surcharge_fee_rules: Any = Field(default_factory=list, description="附加费用（JSON数组）")
    delivery_fee_rules: Any = Field(default_factory=list, description="派送费规则（JSON数组）")
    delivery_time: Optional[str] = Field("", description="交货时效")
    packaging_requirement: Optional[str] = Field("", description="包装要求")
    remark: Optional[str] = Field("", description="备注")
    compensation_policy: Optional[str] = Field("", description="赔付规则")
    status: Optional[int] = Field(1, description="状态, 1=正常")
    filter_rules: Any = Field(default_factory=list, description="过滤规则（JSON数组）")

class PricingRuleCreate(PricingRuleBase):
    pass

class PricingRuleUpdate(PricingRuleBase):
    pass

class LoginForm(BaseModel):
    username: str
    password: str
