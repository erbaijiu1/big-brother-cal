from sqlalchemy.ext.declarative import declarative_base
from db.sqlalchemy_define import DatabaseManager
from utils.logger_config import logger

Base = declarative_base()


from sqlalchemy import Column, String, Text, DateTime, text, Integer, Index, Float


class GoodsClassification(Base):
    __tablename__ = 't_goods_classification'

    category_id = Column(Integer, primary_key=True, autoincrement=True)  # 分类编号 T1/T2等
    main_category = Column(String(50), nullable=False)    # 大类名称（冷冻生肉等）
    sub_examples = Column(Text, nullable=False)           # 子类示例（逗号分隔）
    description = Column(Text, nullable=False)            # 说明字段
    temperature_req = Column(String(100), nullable=False)  # 温控要求（冷链/常温等）
    hazard_level = Column(String(100), nullable=False)     # 危险等级（险/非险/部分险）
    storage_level = Column(String(100), nullable=False)    # 库位等级（A/B/C等）
    create_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))  # 创建时间
    last_modified = Column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))  # 最后修改时间
    status = Column(Integer, default=0, comment='状态, 0:init, 1:ok')
    priority = Column(Integer, default=99, comment='优先级')



class PricingRule(Base):
    __tablename__ = 't_pricing_rule'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    category_id = Column(Integer, nullable=False, comment="关联分类ID（外部维护）")
    channel = Column(String(50), nullable=False, comment="渠道，例如'普A'")
    transport_method = Column(String(50), nullable=False, comment="运输方式，例如'陆运'")
    warehouse = Column(String(50), nullable=False, comment="仓库，例如'深圳仓'")
    min_consumption = Column(Float, nullable=True, comment="最低消费")
    unit_price_rules = Column(Text, nullable=False, comment="单位价规则（按KG和CBM区间定价）")
    discount_price = Column(String(1024), nullable=True, comment="优惠价（如适用）")
    surcharge_fee_rules = Column(Text, nullable=True, comment="附加费用")
    delivery_fee_rules = Column(Text, nullable=True, comment="派送费规则（区间定价）")
    delivery_time = Column(String(100), nullable=True, comment="交货时效")
    packaging_requirement = Column(String(255), nullable=True, comment="包装要求")
    remark = Column(Text, nullable=True, comment="备注")
    compensation_policy = Column(Text, nullable=True, comment="赔付规则")
    status = Column(Integer, default=0, comment='状态, 0:init, 1:ok')
    filter_rules = Column(Text, nullable=True, default='', comment="过滤规则 JSON，结构包含 filters 列表")

    def __repr__(self):
        return f"<PricingRule(category_id={self.category_id}, channel='{self.channel}', transport_method='{self.transport_method}')>"

class ChannelConfig(Base):
    __tablename__ = 't_channel_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    channel_code = Column(String(20), nullable=False, default='', comment="渠道编码，如 普A")
    channel_name = Column(String(100), nullable=False, default='', comment="对应渠道名称，如 港利发")
    surcharge_rules = Column(Text, nullable=True, default='', comment="附加费规则 JSON，结构包含 surcharges 列表")
    filter_rules = Column(Text, nullable=True, default='', comment="过滤规则 JSON，结构包含 filters 列表")
    # 新增一个备注字段
    remark = Column(Text, nullable=True, default='', comment="备注")

    # add channel_code uniq index
    __table_args__ = (
        Index('unique_channel_code', 'channel_code', unique=True),
    )


    def __repr__(self):
        return f"<ChannelSurchargeConfig(channel_code='{self.channel_code}', channel_name='{self.channel_name}')>"


if __name__ == '__main__':
    # 创建数据库连接
    engine = DatabaseManager().get_db_engine()
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        logger.error(f"创建表失败: {e}")
