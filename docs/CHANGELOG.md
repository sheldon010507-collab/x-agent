# CHANGELOG — X-Agent 版本历史

## [3.0.0] — 2026-03-26

### 新增
- **多 LLM 支持**：7 种供应商（Anthropic, OpenAI, Groq, Gemini, OpenRouter, NVIDIA, Ollama）
- **自动调度**：每 2 小时采集热点 + 每日 21:00 复盘
- **Telegram Bot**：11 个命令 + Inline 按钮
- **多 Niche 支持**：7 种预置语气一键切换
- **防封机制**：随机延迟 + 内容变体 + 每日限额
- **复合评分**：4 维评分系统（Relevance 40% + Velocity 30% + Authority 15% + Convergence 15%）
- **last30days 集成**：多平台深度研究（X+Reddit+YouTube+HN+Web+TikTok+IG+Bluesky+Polymarket）

### 变更
- 仓库结构重组：v1/v2 归档到 `archive/`
- 主代码目录统一为 `x-agent/`
- 新增中英双语文档

### 文档
- `UP_AND_RUNNING.md` — 5 分钟上手指南
- `CHANGELOG.md` — 版本历史
- `CONTRIBUTING.md` — 贡献指南

---

## [2.0.0] — 2026-03-24

### 新增
- OpenClaw 集成（x-poster, x-smart-commenter）
- Supabase 数据库支持
- 基础 Telegram Bot

### 变更
- 重构模块架构
- 优化配置管理

---

## [1.0.0] — 2026-03-20

### 新增
- 初始版本
- 基础热点采集
- 单一 LLM 支持
