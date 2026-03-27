# X-Agent v0 Final

**X（Twitter）智能运营 Agent**  
热点监控 + AI 内容生产 + OpenClaw 自动发帖/评论 + 每日复盘

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/sheldon010507-collab/x-agent)
[![Version](https://img.shields.io/badge/version-v0_Final-blue)](https://github.com/sheldon010507-collab/x-agent)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🛡️ V0 Final 核心特性：半自动流程

**强制人工确认** - 所有 AI 生成的内容必须经过用户确认后才能发布，杜绝误操作风险。

### 工作流程

```
AI 生成内容 → 显示 risk_score → 用户选择 → 确认后发布
                ↓
        🟢 低风险 (<50): 可自动发布
        🟡 中风险 (50-79): 建议人工确认  
        🔴 高风险 (≥80): 强制人工确认
```

### Inline 按钮操作

- **🤖 自动发布** - 低风险内容一键发布（<50 分）
- **✅ 人工确认发布** - 所有风险等级都可用
- **🔄 重新生成** - 对内容不满意？重新生成
- **❌ 跳过** - 放弃本次生成

---

## 核心功能

### 🔥 热点监控
- 多平台数据源：X (Twitter)、Reddit、Google Trends
- last30days-skill 深度集成（可选增强）
- 四维评分系统筛选高价值话题

### 🤖 AI 内容生成
- **A 类**：全自动推文（3 条备选）
- **B 类**：视频脚本（需人工拍摄）
- **C 类**：智能评论（带上下文）

### 🎭 Niche Voices
预置 7 种语气风格：

| Niche | 文件 |
|-------|------|
| 成人用品（英国）| `adult_uk.md` |
| AI 工具 | `ai_tools.md` |
| 美妆 | `beauty.md` |
| 健身 | `fitness.md` |
| 加密货币 | `crypto.md` |
| 幽默 | `humor.md` |
| 自定义 | `custom.md` |

### 🛡️ 防封机制
- 随机延迟（10-40 秒）
- 内容变体（emoji/句式随机）
- 每日发布上限（可配置）

---

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env.example` 到 `.env` 并填写：
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
LLM_API_KEY=your_llm_api_key
```

### 3. 运行
```bash
python main.py
```

### 4. Telegram 操作
- `/start` - 查看热点概览
- `/create` - 创建内容（半自动流程）
- `/report` - 查看复盘报告
- `/help` - 帮助

---

## 项目结构

```
x-agent/
├── modules/          # 核心模块
│   ├── bot_v0_final.py   # V0 Final 半自动 Bot
│   ├── research.py       # 热点研究
│   ├── scorer.py         # 评分系统
│   ├── generator.py      # 内容生成
│   ├── database.py       # 数据库操作
│   └── openclaw_bridge.py # OpenClaw 集成
├── tests/            # 测试文件
├── docs/             # 文档
└── migrations/       # 数据库迁移
```

---

## 测试

运行 V0 Final 核心测试：
```bash
python -m pytest tests/test_v0_final.py -v
```

测试覆盖：
- ✅ Research 模块（last30days 集成）
- ✅ Scorer 模块（risk_score 计算）
- ✅ Bot 流程（半自动确认）
- ✅ Database（状态流转）

---

## 文档

- [上手指南](docs/UP_AND_RUNNING.md)
- [部署指南](docs/DEPLOYMENT.md)
- [贡献指南](CONTRIBUTING.md)
- [变更日志](docs/CHANGELOG.md)

---

## License

MIT License - 详见 [LICENSE](LICENSE)

---

**用 ❤️ 构建 by sheldon010507-collab**
