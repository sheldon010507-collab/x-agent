#!/bin/bash

# start_mac_services.sh - Mac 多进程启动脚本
# 启动: 主应用 + OpenClaw Agent + Report Agent

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  X-Agent Mac 多进程启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚠️  虚拟环境不存在，创建中...${NC}"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install -r "$PROJECT_DIR/requirements.txt"
else
    source "$VENV_DIR/bin/activate"
fi

# 检查 .env 文件
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}❌ .env 文件不存在${NC}"
    echo "请复制 .env.example 并填入配置："
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查完成${NC}"
echo ""

# 启动函数
start_service() {
    local service_name=$1
    local script_path=$2
    local log_file="$LOG_DIR/${service_name}.log"

    echo -e "${YELLOW}启动 $service_name...${NC}"

    nohup python3 "$script_path" > "$log_file" 2>&1 &
    local pid=$!

    sleep 2

    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✅ $service_name 已启动 (PID: $pid)${NC}"
        echo "$pid" > "$LOG_DIR/${service_name}.pid"
        return 0
    else
        echo -e "${RED}❌ $service_name 启动失败${NC}"
        echo "查看日志: tail -f $log_file"
        return 1
    fi
}

# 启动所有服务
echo -e "${YELLOW}正在启动服务...${NC}"
echo ""

start_service "main" "$PROJECT_DIR/main.py"
sleep 2

start_service "openclaw_agent" "$PROJECT_DIR/agents/openclaw_agent.py"
sleep 2

start_service "report_agent" "$PROJECT_DIR/agents/report_agent.py"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✨ 所有服务已启动${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo "📋 服务信息:"
echo "  • 主应用: Telegram Bot (PID: $(cat $LOG_DIR/main.pid 2>/dev/null || echo 'N/A'))"
echo "  • OpenClaw Agent (PID: $(cat $LOG_DIR/openclaw_agent.pid 2>/dev/null || echo 'N/A'))"
echo "  • Report Agent (PID: $(cat $LOG_DIR/report_agent.pid 2>/dev/null || echo 'N/A'))"
echo ""

echo "📝 日志位置:"
echo "  • $LOG_DIR/main.log"
echo "  • $LOG_DIR/openclaw_agent.log"
echo "  • $LOG_DIR/report_agent.log"
echo ""

echo "🔍 实时监控:"
echo "  tail -f $LOG_DIR/main.log"
echo "  tail -f $LOG_DIR/openclaw_agent.log"
echo "  tail -f $LOG_DIR/report_agent.log"
echo ""

echo "🛑 停止所有服务:"
echo "  bash stop_mac_services.sh"
echo ""
