FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖列表
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p data/research logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC
ENV APP_ENTRYPOINT=main.py

# 启动应用（默认 Telegram Bot；API 服务通过 APP_ENTRYPOINT=api.py 覆盖）
CMD ["sh", "-c", "python $APP_ENTRYPOINT"]
