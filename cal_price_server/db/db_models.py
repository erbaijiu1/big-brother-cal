from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from db.sqlalchemy_define import DatabaseManager
from utils.logger_config import logger

Base = declarative_base()


from sqlalchemy import Column, String, Text, DateTime, text, Integer, Index, Float, Boolean, ForeignKey


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
    customer_price_tiers = Column(Text, nullable=True, default='', comment='对客阶梯价 JSON')
    price_tiers_updated_at = Column(DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP"), comment='对客阶梯价更新时间')
    warehouse_acceptance_policy = Column(String(20), nullable=False, default='MANUAL_CONFIRM', comment='入仓策略')
    acceptance_notice = Column(String(255), nullable=True, default='', comment='入仓策略说明')


class GoodsPriceTierHistory(Base):
    __tablename__ = 't_goods_price_tier_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    category_id = Column(Integer, nullable=False, index=True, comment='货物分类ID')
    main_category = Column(String(50), nullable=False, comment='分类名称快照')
    config_snapshot = Column(Text, nullable=False, comment='对客阶梯价配置快照 JSON')
    changed_by_id = Column(Integer, nullable=True, comment='操作管理员ID')
    changed_by_name = Column(String(50), nullable=True, comment='操作管理员账号')
    changed_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment='变更时间')


class CooperationQuoteConfig(Base):
    """长期合作客户的品类报价卡，与单票计价规则完全隔离。"""

    __tablename__ = 't_cooperation_quote_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    category_id = Column(Integer, nullable=False, unique=True, index=True, comment='货物分类ID')
    enabled = Column(Boolean, nullable=False, default=True, comment='是否启用')
    currency = Column(String(10), nullable=False, default='CNY', comment='币种')
    price_tiers = Column(Text, nullable=False, comment='合作阶梯价 JSON')
    delivery_base_fee = Column(Float, nullable=True, comment='香港派送基础费用')
    delivery_included_weight = Column(Float, nullable=True, comment='基础派送费包重 kg')
    delivery_excess_rate = Column(Float, nullable=True, comment='超重派送费 元/kg')
    sea_crossing_notice = Column(String(255), nullable=True, default='', comment='港岛过海说明')
    upstairs_notice = Column(Text, nullable=True, default='', comment='上楼费用说明')
    cutoff_text = Column(String(255), nullable=True, default='', comment='入仓截单说明')
    eta_text = Column(String(255), nullable=True, default='', comment='运输时效说明')
    customer_notice = Column(Text, nullable=True, default='', comment='其他对客说明')
    config_updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        comment='配置更新时间',
    )



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
    region_rules = Column(Text, nullable=True, comment="区域规则数组，JSON格式")

    def __repr__(self):
        return f"<PricingRule(category_id={self.category_id}, channel='{self.channel}', transport_method='{self.transport_method}')>"

class ChannelConfig(Base):
    __tablename__ = 't_channel_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    channel_code = Column(String(20), nullable=False, default='', comment="渠道编码，如 普A")
    channel_name = Column(String(100), nullable=False, default='', comment="对应渠道名称，如 港利发")
    receiving_address = Column(Text, nullable=True, default='', comment="渠道收货地址")
    customer_quote_config = Column(Text, nullable=True, default='', comment="对客报价展示配置 JSON")
    config_updated_at = Column(DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP"), comment="对客配置更新时间")
    surcharge_rules = Column(Text, nullable=True, default='', comment="附加费规则 JSON，结构包含 surcharges 列表")
    filter_rules = Column(Text, nullable=True, default='', comment="过滤规则 JSON，结构包含 filters 列表")
    # 新增一个备注字段
    remark = Column(Text, nullable=True, default='', comment="备注")
    delete_flag = Column(Integer, default=0, comment='删除标志，0:未删除，1:已删除')

    # add channel_code uniq index
    __table_args__ = (
        Index('unique_channel_code', 'channel_code', unique=True),
    )


    def __repr__(self):
        return f"<ChannelSurchargeConfig(channel_code='{self.channel_code}', channel_name='{self.channel_name}')>"


class ChannelQuoteConfigHistory(Base):
    __tablename__ = 't_channel_quote_config_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    channel_id = Column(Integer, ForeignKey('t_channel_config.id'), nullable=False, index=True, comment="渠道ID")
    channel_code = Column(String(20), nullable=False, comment="渠道编码快照")
    config_snapshot = Column(Text, nullable=False, comment="对客报价配置快照 JSON")
    changed_by_id = Column(Integer, nullable=True, comment="操作管理员ID")
    changed_by_name = Column(String(50), nullable=True, comment="操作管理员账号")
    changed_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), comment="变更时间")

class AdminUser(Base):
    __tablename__ = "admin_user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)  # 可以加密
    nickname = Column(String(50), default="")
    status = Column(Integer, default=1)  # 1=正常 2=禁用


class District(Base):
    __tablename__ = "district"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_cn = Column(String(32), nullable=False, unique=True)
    name_en = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SubDistrict(Base):
    __tablename__ = "sub_district"
    id = Column(Integer, primary_key=True, autoincrement=True)
    district_id = Column(Integer, nullable=False)
    name_cn = Column(String(32), nullable=False)
    name_en = Column(String(64), nullable=False)
    is_remote = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AreaCategory(Base):
    __tablename__ = "area_category"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AreaCategoryMap(Base):
    __tablename__ = "area_category_map"
    category_id = Column(Integer, primary_key=True)
    sub_district_id = Column(Integer, primary_key=True)


if __name__ == '__main__':
    # 创建数据库连接
    engine = DatabaseManager().get_db_engine()
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        logger.error(f"创建表失败: {e}")
