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


# 至少挣多少钱
MIN_EARN_MONEY = os.getenv("MIN_EARN_MONEY", 30)
# 配置挣取的比例
EARN_MONEY_RATIO = os.getenv("EARN_MONEY_RATIO", 0.3)
# 加额外费用的项
EXTRA_FEE_ITEMS = os.getenv("EXTRA_FEE_ITEMS", "unit_price")
