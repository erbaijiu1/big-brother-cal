# -*- coding: utf-8 -*-
JSON_AS_ASCII = False
JSONIFY_MIMETYPE = "application/json;charset=utf-8"
LOG_LEVEL = 10 #debug

DEFAULT_ENV = "test"
DEFAULT_PORT = 8080

PORT = 7001


import os

# 数据库连接配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Gmcc@123")
DB_NAME = os.getenv("DB_NAME", "db_prize_cal")


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://10.233.243.163:11434/v1/chat/completions")
OLLAMA_URL2 = os.getenv("OLLAMA_URL2", "http://10.233.243.163:11435/v1/chat/completions")

TC_CLOUD_BOT_APP_KEY = os.getenv("TC_CLOUD_BOT_APP_KEY", "mXCsuwon")
TC_CLOUD_CHAT_SEARCH_ONLINE_URL = os.getenv("TC_CLOUD_CHAT_SEARCH_ONLINE_URL", "https://wss.lke.cloud.tencent.com/v1/qbot/chat/sse")

VLLM_DEEPSEEK_URL = os.getenv("VLLM_DEEPSEEK_URL", "http://10.233.243.163:8101/v1/chat/completions")
VLLM_QWQ_URL = os.getenv("VLLM_QWQ_URL", "http://10.233.243.163:8102/v1/chat/completions")

# 日志路径及文字名全路径配置
GLOBAL_LOG_PATH = os.getenv("GLOBAL_LOG_PATH", "./logs/server.log")

# 上下文最大使用的历史记录
CHAT_HISTORY_MAX_SIZE = os.getenv("CHAT_HISTORY_MAX_SIZE", 10)
