FROM python:3.10-slim
WORKDIR /app
COPY . .
# 安装依赖，使用国内镜像源（推荐阿里云或清华）
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/  \
    --trusted-host mirrors.aliyun.com

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088"]

