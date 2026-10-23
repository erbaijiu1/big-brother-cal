# -*- coding: utf-8 -*-
import os

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123")
DB_NAME = os.getenv("DB_NAME", "db_prize_cal")


# 日志路径及文字名全路径配置
GLOBAL_LOG_PATH = os.getenv("GLOBAL_LOG_PATH", "./logs/server.log")


# 最低利润额。对客利润取 max(最低利润额, 成本 * 利润率)。
MIN_EARN_MONEY = float(os.getenv("MIN_EARN_MONEY", "30"))
# 成本利润率，例如 0.3 表示成本的 30%。
EARN_MONEY_RATIO = float(os.getenv("EARN_MONEY_RATIO", "0.3"))
# 加额外费用的项
EXTRA_FEE_ITEMS = os.getenv("EXTRA_FEE_ITEMS", "unit_price")

# AI 客服等内部调用方访问对客报价聚合接口时使用的服务令牌。
CUSTOMER_QUOTE_SERVICE_TOKEN = os.getenv("CUSTOMER_QUOTE_SERVICE_TOKEN", "")
