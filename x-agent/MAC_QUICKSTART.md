# 🚀 Mac 快速启动 (5 分钟)

## 一键启动

```bash
cd /path/to/x-agent/x-agent

# 1. 创建虚拟环境和安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
nano .env  # 填入你的配置

# 3. 启动所有服务
chmod +x start_mac_services.sh
./start_mac_services.sh
```

---

## 📋 环境变量必填项

打开 `.env` 文件，填入以下配置：

```env
# Telegram Bot Token (从 @BotFather 获取)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# OpenClaw API 配置
OPENCLAW_API_ENDPOINT=http://localhost:8080
OPENCLAW_API_KEY=your_openclaw_api_key_here

# Supabase 数据库配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Anthropic (Claude) API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# 报告配置
REPORT_FREQUENCY=daily      # 每日报告
REPORT_HOUR=21              # 晚上9点生成
```

---

## ✅ 验证启动成功

```bash
# 查看日志
tail -f logs/main.log
tail -f logs/openclaw_agent.log
tail -f logs/report_agent.log

# 应该看到类似的输出：
# [INFO] ✨ X-Agent Bot 已启动
# [INFO] ✨ OpenClaw Agent 已启动
# [INFO] ✨ Report Agent 已启动
```

---

## 🎮 开始使用

### 从 Telegram 发送命令

```
/start                    # 启动 Bot，查看热点
/research AI trends      # 研究特定话题
/create                  # 创建内容
/report                  # 查看报告
```

---

## 📊 三个进程在做什么

### 1️⃣ Main (Telegram Bot)
- 接收你的命令
- 研究热点
- 生成 A/B/C 类内容
- 显示二步审核界面

### 2️⃣ OpenClaw Agent
- 监听待发布内容
- 通过 OpenClaw 发布到 X
- 执行防封机制

### 3️⃣ Report Agent
- 每天晚上 21:00 生成报告
- 分析多平台数据 (Reddit, HackerNews, Google Trends)
- 推送报告到 Telegram

---

## 🛑 停止所有服务

```bash
./stop_mac_services.sh
```

---

## 🐛 常见问题

### Q1: 启动失败？
```bash
# 检查日志
tail -f logs/main.log

# 检查 .env 是否填写正确
cat .env | grep -E "TELEGRAM|OPENCLAW|SUPABASE"
```

### Q2: OpenClaw Agent 无法连接？
```bash
# 确认 OpenClaw 在运行
curl http://localhost:8080/health

# 检查配置
grep OPENCLAW .env
```

### Q3: 报告没有生成？
```bash
# 检查 Report Agent 是否运行
ps aux | grep report_agent

# 查看日志
tail -f logs/report_agent.log

# 检查时间配置
grep REPORT .env
```

---

## 📚 完整文档

详细部署指南见: `docs/MAC_DEPLOYMENT.md`

---

## 🆘 需要帮助？

1. 查看日志: `tail -f logs/*.log`
2. 运行诊断: `python3 -c "import modules; print('OK')"`
3. 检查进程: `ps aux | grep python3`

---

**祝你使用愉快！** 🎉
