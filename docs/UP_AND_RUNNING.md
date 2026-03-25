# 5分钟上手 Checklist

## 准备工作

确保你有以下账号：
- [ ] Telegram Bot Token（从 @BotFather 获取）
- [ ] Supabase 项目（免费版即可）
- [ ] 至少一个 LLM API Key（Claude/OpenAI/Groq/Gemini 任选）

---

## 步骤

### 1. 克隆仓库
```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
```

编辑 `.env`，填入以下必填项：
```env
TELEGRAM_BOT_TOKEN=你的bot_token
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=你的supabase_key
ANTHROPIC_API_KEY=你的claude_key
# 或其他 LLM Key
```

### 4. 初始化数据库
在 Supabase SQL Editor 中执行：
```sql
-- 执行 migrations/001_initial_schema.sql
```

或使用 Supabase CLI：
```bash
supabase db push
```

### 5. 启动
```bash
python main.py
```

或使用 PM2 常驻运行：
```bash
pm2 start main.py --name x-agent --interpreter python3
```

### 6. 验证
1. 打开 Telegram
2. 找到你的 Bot
3. 发送 `/start`
4. 看到热点概览即成功！

### 7. 切换 Niche
```
/set_niche adult_uk
```

### 8. 查看热点
```
/trends
```

### 9. 生成内容
```
/create
```

### 10. 查看复盘
```
/report
```

---

## 常见问题

### Q: last30days 命令未找到？
```bash
clawhub install last30days
```

### Q: OpenClaw 未启动？
```bash
openclaw gateway start
```

### Q: 数据库连接失败？
检查 `.env` 中的 Supabase URL 和 Key 是否正确。

---

## 下一步

- 📖 阅读 [完整文档](DEPLOYMENT.md)
- 🎭 尝试不同 Niche
- ⚙️ 调整自动化设置
- 📊 查看每日复盘

祝使用愉快！ 🚀
