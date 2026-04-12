#!/bin/bash

# ============================================
# X-Agent + OpenClaw 快速启动脚本
# ============================================

set -e

echo "🚀 X-Agent + OpenClaw 启动向导"
echo "================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "${BLUE}[1/5] 检查 Python 版本...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python 3${NC}"
    echo "请安装 Python 3.11 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}✅ Python 版本: $PYTHON_VERSION${NC}"
echo ""

# 检查虚拟环境
echo -e "${BLUE}[2/5] 检查虚拟环境...${NC}"
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
    echo -e "${GREEN}✅ 虚拟环境已创建${NC}"
else
    echo -e "${GREEN}✅ 虚拟环境已存在${NC}"
fi
echo ""

# 激活虚拟环境
echo -e "${BLUE}[3/5] 激活虚拟环境...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
echo ""

# 安装/更新依赖
echo -e "${BLUE}[4/5] 安装依赖...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✅ 依赖已安装${NC}"
echo ""

# 检查环境变量
echo -e "${BLUE}[5/5] 检查环境变量...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️ 未找到 .env 文件${NC}"
    echo "正在创建 .env 模板..."

    cat > .env << 'EOF'
# ========== OpenClaw 配置 ==========
OPENCLAW_ENABLED=true
OPENCLAW_API_KEY=your_api_key_here
OPENCLAW_API_SECRET=your_api_secret_here
OPENCLAW_API_ENDPOINT=http://localhost:8080

# ========== 防封机制 ==========
DELAY_MIN=10
DELAY_MAX=40
MAX_POSTS_PER_DAY=5
MAX_COMMENTS_PER_DAY=15
MAX_LIKES_PER_DAY=30

# ========== Telegram Bot ==========
TELEGRAM_BOT_TOKEN=your_bot_token

# ========== Supabase ==========
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# ========== LLM ==========
ANTHROPIC_API_KEY=your_anthropic_key
EOF

    echo -e "${YELLOW}📝 已创建 .env，请编辑填入您的配置${NC}"
    echo "编辑命令: nano .env"
    exit 1
else
    # 检查必要的配置项
    if grep -q "your_api_key_here" .env; then
        echo -e "${YELLOW}⚠️ .env 中仍有默认值，请编辑配置${NC}"
        echo "编辑命令: nano .env"
        exit 1
    fi
    echo -e "${GREEN}✅ 环境变量已配置${NC}"
fi
echo ""

# 提示启动选项
echo "================================================"
echo -e "${GREEN}✅ 所有检查通过，准备启动${NC}"
echo "================================================"
echo ""
echo "请选择启动方式："
echo "  1) 直接运行（前台）"
echo "  2) 后台运行（PM2）"
echo "  3) Docker 运行"
echo "  4) 仅启动 OpenClaw"
echo ""
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        echo -e "${BLUE}启动 X-Agent（前台模式）...${NC}"
        python main.py
        ;;
    2)
        echo -e "${BLUE}启动 X-Agent（后台模式 - PM2）...${NC}"

        # 检查 PM2
        if ! command -v pm2 &> /dev/null; then
            echo "安装 PM2..."
            npm install -g pm2
        fi

        pm2 start main.py --name "x-agent" --interpreter "python" \
            --env "PATH=./venv/bin:$PATH"
        pm2 save

        echo -e "${GREEN}✅ X-Agent 已启动${NC}"
        echo "查看日志: pm2 logs x-agent"
        echo "查看状态: pm2 status"
        ;;
    3)
        echo -e "${BLUE}启动 X-Agent（Docker 模式）...${NC}"

        # 检查 Docker
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}❌ 未找到 Docker${NC}"
            echo "请先安装 Docker"
            exit 1
        fi

        # 构建镜像
        docker build -t x-agent .

        # 运行容器
        docker run -d --name x-agent \
            --env-file .env \
            -v $(pwd)/data:/app/data \
            x-agent

        echo -e "${GREEN}✅ Docker 容器已启动${NC}"
        echo "查看日志: docker logs -f x-agent"
        ;;
    4)
        echo -e "${BLUE}启动 OpenClaw 服务器...${NC}"

        # 检查 Docker
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}❌ 需要 Docker 来运行 OpenClaw${NC}"
            exit 1
        fi

        # 创建 docker-compose.yml
        cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  openclaw:
    image: openclaw/openclaw:latest
    ports:
      - "8080:8080"
    environment:
      - OPENCLAW_PORT=8080
      - LOG_LEVEL=info
    volumes:
      - openclaw_data:/app/data
    restart: unless-stopped

volumes:
  openclaw_data:
EOF

        echo "启动 OpenClaw..."
        docker-compose up -d

        echo -e "${GREEN}✅ OpenClaw 已启动${NC}"
        echo "等待 10 秒初始化..."
        sleep 10

        # 检查健康状态
        if curl -s http://localhost:8080/health | grep -q "ok"; then
            echo -e "${GREEN}✅ OpenClaw 运行正常${NC}"
            echo ""
            echo "现在可以运行 X-Agent:"
            echo "  python main.py"
        else
            echo -e "${RED}⚠️ OpenClaw 启动可能需要更多时间${NC}"
        fi
        ;;
    *)
        echo -e "${RED}❌ 无效的选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "================================================"
echo -e "${GREEN}启动完成！${NC}"
echo "================================================"
echo ""
echo "有用的命令:"
echo "  • 查看日志: pm2 logs x-agent"
echo "  • 停止服务: pm2 stop x-agent"
echo "  • 重启服务: pm2 restart x-agent"
echo "  • Telegram Bot 命令: /start, /create, /stats"
echo ""
echo "📚 完整文档: docs/OPENCLAW_DEPLOYMENT.md"
echo ""
