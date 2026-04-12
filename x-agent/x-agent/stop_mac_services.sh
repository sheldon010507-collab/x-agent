#!/bin/bash

# stop_mac_services.sh - 停止所有服务

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/logs"

echo -e "${YELLOW}🛑 停止所有服务...${NC}"
echo ""

stop_service() {
    local service_name=$1
    local pid_file="$LOG_DIR/${service_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null || true
            sleep 1
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null || true
            fi
            rm -f "$pid_file"
            echo -e "${GREEN}✅ $service_name 已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  $service_name 未运行${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}⚠️  $service_name PID 文件不存在${NC}"
    fi
}

stop_service "main"
stop_service "openclaw_agent"
stop_service "report_agent"

echo ""
echo -e "${GREEN}✅ 所有服务已停止${NC}"
