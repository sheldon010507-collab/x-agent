# Mac 多进程部署指南

## 🎯 架构概述

X-Agent on Mac 采用三进程架构：

```
┌──────────────────────────────────────────────┐
│  Main Process: Telegram Bot                  │
│  (用户交互、内容生成、二步审核)              │
└────────────┬─────────────────────────────────┘
             │
      ┌──────┴──────┬──────────────┐
      ↓             ↓              ↓
┌─────────────┐ ┌──────────────┐ ┌────────────┐
│OpenClaw Agt │ │Report Agent  │ │ Database   │
│(发布控制)   │ │(分析报告)    │ │ (Supabase) │
└─────────────┘ └──────────────┘ └────────────┘
```

---

## 📦 前置条件

- **Mac OS**: 10.15+
- **Python**: 3.11+
- **Node.js**: 18+ (可选，用于 PM2)
- **Xcode Command Line Tools**: `xcode-select --install`

---

## 🚀 快速部署（5 分钟）

### 1️⃣ 克隆和初始化

```bash
# 克隆项目
cd /path/to/x-agent

# 进入项目
cd x-agent

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs
```

### 2️⃣ 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置（用你的编辑器打开）
nano .env
```

**必填配置项**:

```env
# ========== Telegram Bot ==========
TELEGRAM_BOT_TOKEN=your_token_from_botfather

# ========== OpenClaw ==========
OPENCLAW_API_ENDPOINT=http://localhost:8080
OPENCLAW_API_KEY=your_openclaw_api_key

# ========== Supabase (数据库) ==========
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key

# ========== LLM (AI 模型) ==========
ANTHROPIC_API_KEY=sk-ant-your-key

# ========== 报告配置 ==========
REPORT_FREQUENCY=daily          # daily 或 weekly
REPORT_HOUR=21                  # 几点生成报告 (0-23)
REPORT_DAY_OF_WEEK=0            # 周报的日期 (0=Sunday)

# ========== 防封配置 ==========
DELAY_MIN=10
DELAY_MAX=40
MAX_POSTS_PER_DAY=10
```

### 3️⃣ 启动所有服务

```bash
# 给脚本执行权限
chmod +x start_mac_services.sh
chmod +x stop_mac_services.sh

# 启动所有服务
./start_mac_services.sh
```

✅ **输出应该是这样**:

```
========================================
  X-Agent Mac 多进程启动脚本
========================================

✅ 环境检查完成

正在启动服务...

✅ main 已启动 (PID: 12345)
✅ openclaw_agent 已启动 (PID: 12346)
✅ report_agent 已启动 (PID: 12347)

========================================
  ✨ 所有服务已启动
========================================

📋 服务信息:
  • 主应用: Telegram Bot (PID: 12345)
  • OpenClaw Agent (PID: 12346)
  • Report Agent (PID: 12347)

📝 日志位置:
  • /path/to/logs/main.log
  • /path/to/logs/openclaw_agent.log
  • /path/to/logs/report_agent.log
```

---

## 🔄 三个 Agent 详解

### 1. Main Process (Telegram Bot)

**职责**:
- 接收用户命令
- 研究热点
- 生成内容 (A/B/C 类)
- 显示二步审核界面
- 将确认的内容写入数据库

**启动命令**: `python3 main.py`

**日志**:
```bash
tail -f logs/main.log
```

---

### 2. OpenClaw Agent

**职责**:
- 监听数据库中的待发布内容
- 通过 OpenClaw 执行 X 发布
- 执行防封机制 (延迟、变体、限额)
- 更新发布状态

**启动命令**: `python3 agents/openclaw_agent.py`

**日志**:
```bash
tail -f logs/openclaw_agent.log
```

**监控发布队列**:
```bash
# 查看待发布内容
curl -X GET http://localhost:8080/api/queue

# 查看已发布内容
curl -X GET http://localhost:8080/api/published
```

---

### 3. Report Agent

**职责**:
- 定时收集多平台数据 (Reddit, HackerNews, Google Trends)
- 分析趋势
- 生成综合报告
- 推送报告给用户 (Telegram/邮件)

**启动命令**: `python3 agents/report_agent.py`

**日志**:
```bash
tail -f logs/report_agent.log
```

**报告生成时间**:
- `REPORT_FREQUENCY=daily` → 每天 `REPORT_HOUR` 时刻
- `REPORT_FREQUENCY=weekly` → 每周 `REPORT_DAY_OF_WEEK` 的 `REPORT_HOUR` 时刻

---

## 📊 数据流

```
1. 用户 (Telegram)
   ↓
2. Main Process
   • 研究热点
   • 生成内容
   • 显示二步审核
   ↓
3. Database (Supabase)
   • 存储待发布内容
   ↓
4. OpenClaw Agent
   • 监听队列
   • 执行发布
   ↓
5. X (Twitter)
   • 发布成功

━━━━━━━━━━━━━━━━━

1. Report Agent (定时)
   • 收集多平台数据
   • 分析趋势
   ↓
2. Database (Supabase)
   • 存储报告
   ↓
3. Telegram Bot
   • 推送通知给用户
```

---

## 🛠️ 常用命令

### 启动/停止

```bash
# 启动所有服务
./start_mac_services.sh

# 停止所有服务
./stop_mac_services.sh

# 查看运行中的服务
ps aux | grep "python3 main\|agents"
```

### 实时监控

```bash
# 监控所有日志
tail -f logs/*.log

# 监控特定服务
tail -f logs/openclaw_agent.log
tail -f logs/report_agent.log
```

### 查看服务状态

```bash
# 检查 PID 是否存在
cat logs/main.pid | xargs ps -p

# 查看进程资源使用
ps aux | grep python3
```

### 手动重启单个服务

```bash
# 停止 OpenClaw Agent
kill $(cat logs/openclaw_agent.pid)

# 重启
python3 agents/openclaw_agent.py > logs/openclaw_agent.log 2>&1 &
```

---

## 🐛 故障排除

### 问题 1: 启动脚本权限不足

```bash
chmod +x start_mac_services.sh
chmod +x stop_mac_services.sh
./start_mac_services.sh
```

### 问题 2: .env 文件不存在

```bash
cp .env.example .env
nano .env  # 填入配置
./start_mac_services.sh
```

### 问题 3: 虚拟环境出错

```bash
# 删除旧环境
rm -rf venv

# 重新创建
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 4: OpenClaw Agent 无法连接

```bash
# 检查 OpenClaw 是否运行
curl -X GET http://localhost:8080/health

# 查看配置
grep "OPENCLAW" .env

# 查看日志
tail -f logs/openclaw_agent.log
```

### 问题 5: 报告未生成

```bash
# 检查 Report Agent 是否运行
ps aux | grep report_agent

# 查看日志
tail -f logs/report_agent.log

# 验证配置
grep "REPORT_" .env
```

---

## 📈 生产部署建议

### 1. 使用 PM2 管理进程

```bash
# 安装 PM2
npm install -g pm2

# 创建 ecosystem.config.js
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'x-agent-main',
      script: 'main.py',
      interpreter: 'python3',
      env: {
        NODE_ENV: 'production'
      },
      error_file: 'logs/main_error.log',
      out_file: 'logs/main.log'
    },
    {
      name: 'x-agent-openclaw',
      script: 'agents/openclaw_agent.py',
      interpreter: 'python3',
      error_file: 'logs/openclaw_error.log',
      out_file: 'logs/openclaw_agent.log'
    },
    {
      name: 'x-agent-report',
      script: 'agents/report_agent.py',
      interpreter: 'python3',
      error_file: 'logs/report_error.log',
      out_file: 'logs/report_agent.log'
    }
  ]
};
EOF

# 启动
pm2 start ecosystem.config.js

# 设置开机自启
pm2 startup
pm2 save
```

### 2. 日志轮转

```bash
# 安装 logrotate
brew install logrotate

# 配置日志轮转
cat > /usr/local/etc/logrotate.d/x-agent << 'EOF'
/path/to/x-agent/logs/*.log {
  daily
  rotate 7
  compress
  delaycompress
  notifempty
  create 0640 user group
  sharedscripts
}
EOF
```

### 3. 监控和告警

```bash
# 创建监控脚本
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
  for service in main openclaw_agent report_agent; do
    if ! ps -p $(cat logs/${service}.pid 2>/dev/null) > /dev/null 2>&1; then
      echo "⚠️  $service 崩溃，重启中..."
      python3 agents/${service}.py > logs/${service}.log 2>&1 &
    fi
  done
  sleep 60
done
EOF

chmod +x monitor.sh
./monitor.sh &
```

---

## 📚 相关文档

- [OpenClaw 部署](./OPENCLAW_DEPLOYMENT.md)
- [数据存储架构](./DATA_STORAGE.md)
- [API 文档](./API.md)

---

## 🆘 获取帮助

```bash
# 查看所有日志
ls -la logs/

# 搜索错误
grep -i "error\|exception" logs/*.log

# 查看特定时间的日志
sed -n '2024-01-01/,2024-01-02p' logs/main.log
```

---

**最后更新**: 2026-03-29
**维护者**: X-Agent Team
