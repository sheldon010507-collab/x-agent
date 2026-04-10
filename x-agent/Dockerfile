FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxss1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖列表
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright Chromium 浏览器
RUN playwright install chromium

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
