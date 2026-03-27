# Security Policy

## API Key 管理规范

### 存储原则

- 所有 API Key **必须**通过 `.env` 文件或系统环境变量注入，禁止硬编码到源代码中。
- `.env` 文件已列入 `.gitignore`，不得提交到版本控制。
- 生产环境建议使用密钥管理服务（如 AWS Secrets Manager、HashiCorp Vault）。

### 最小权限原则

| Key | 所需权限 |
|-----|---------|
| `ANTHROPIC_API_KEY` | 仅消息创建（`messages:write`） |
| `OPENAI_API_KEY` | 仅 chat completions |
| `GROQ_API_KEY` | 仅 chat completions |
| `SUPABASE_KEY` | 仅对应表的 `SELECT/INSERT/UPDATE` |
| `TELEGRAM_BOT_TOKEN` | 仅 Bot API 操作 |

### Key 轮换建议

- Anthropic / OpenAI / Groq：每 90 天轮换一次
- Supabase：权限最小化，使用 Row Level Security (RLS)
- Telegram Bot Token：如怀疑泄露立即通过 @BotFather 撤销

---

## 防封机制说明

X-Agent 通过 OpenClaw Bridge 与 X/Twitter 交互，内置以下防封机制：

1. **风险评分拦截**：risk_score ≥ 80 的内容不允许自动发布，需人工确认。
2. **每日限额**：评论默认限制 15 条/天，点赞限制 30 条/天，转发限制 10 条/天（可通过 Automation Settings 调整）。
3. **内容审核**：所有内容默认进入 `draft` 状态，经 Telegram Bot 人工确认（`/confirm`）后才能发布。
4. **关键词过滤**：`generator.py` 对 `crypto`、`adult`、`onlyfans` 等高风险关键词自动提高风险分。

---

## 依赖安全扫描

### 自动化（CI/CD）

CI 流水线包含 `bandit` 静态安全扫描，检测以下问题：
- 硬编码密钥
- 不安全的随机数生成
- SQL 注入风险（bandit B608）
- 已知不安全的库使用

### 手动扫描

```bash
# 运行 bandit（严重 + 高危）
bandit -r modules/ -ll

# 检查依赖漏洞
pip install pip-audit
pip-audit -r requirements.txt
```

---

## 已知安全约束

| 约束 | 原因 |
|------|------|
| 不存储明文密码 | 系统无需用户密码认证，仅 Telegram user_id 鉴权 |
| Supabase RLS | 确保 Bot 只能访问自己的数据，不跨租户泄露 |
| 发布前人工审核 | 防止 LLM 幻觉生成违规内容导致账号封禁 |

---

## 漏洞报告

如发现安全漏洞，请通过仓库 Issues 提交，标记 `security` 标签，我们将在 48 小时内响应。
