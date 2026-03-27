# X-Agent v2.0 部署指南

## 📋 部署前检查清单

- [ ] Python 3.11+ 已安装
- [ ] Supabase 项目已创建
- [ ] Telegram Bot 已创建
- [ ] 至少一个 LLM API Key 已获取
- [ ] Reddit API 凭证（可选）

---

## 🖥️ 本地部署

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent-v2

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

**必需配置**:
```
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
ANTHROPIC_API_KEY=your_anthropic_key  # 或其他 LLM
```

### 3. 初始化数据库

```bash
# 在 Supabase SQL 编辑器中执行
# 复制 migrations/001_initial_schema.sql 的内容
```

### 4. 运行

```bash
python main.py
```

---

## ☁️ VPS 部署

### 使用 PM2 常驻运行

```bash
# 安装 PM2
npm install -g pm2

# 创建 ecosystem.config.js
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'x-agent',
    script: 'main.py',
    interpreter: 'python3',
    cwd: '/path/to/x-agent-v2',
    env: {
      NODE_ENV: 'production'
    },
    watch: false,
    autorestart: true,
    max_restarts: 5,
    restart_delay: 3000
  }]
}
EOF

# 启动
pm2 start ecosystem.config.js

# 保存配置
pm2 save

# 设置开机启动
pm2 startup
```

### 查看日志

```bash
pm2 logs x-agent
```

### 重启服务

```bash
pm2 restart x-agent
```

---

## 🔐 生产环境安全配置

### 1. 环境变量安全

```bash
# 设置正确的文件权限
chmod 600 .env

# 确保 .env 在 .gitignore 中
echo ".env" >> .gitignore
```

### 2. Supabase 安全

- 启用 Row Level Security (RLS)
- 限制 API Key 权限
- 设置 IP 白名单（如果支持）

### 3. Telegram Bot 安全

- 不要在公开渠道分享 Bot Token
- 定期检查 Bot 的管理员列表

---

## 🔄 更新部署

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
pm2 restart x-agent
```

---

## 📊 监控

### 健康检查

```bash
# 检查服务状态
pm2 status

# 查看实时日志
pm2 logs x-agent --lines 100
```

### 日志位置

- PM2 日志: `~/.pm2/logs/`
- 应用日志: 控制台输出

---

## 🐛 常见问题

### Q: Bot 无响应

1. 检查 Bot Token 是否正确
2. 检查网络连接
3. 查看 PM2 日志: `pm2 logs x-agent`

### Q: 数据库连接失败

1. 检查 SUPABASE_URL 和 SUPABASE_KEY
2. 检查 Supabase 项目状态
3. 确认 IP 未被限制

### Q: LLM 调用失败

1. 检查 API Key 是否有效
2. 检查 API 额度是否用尽
3. 尝试切换其他供应商: `/llm` 命令

---

## 📞 支持

如有问题，请在 GitHub Issues 提交。
