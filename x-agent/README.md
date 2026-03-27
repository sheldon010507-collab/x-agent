# X-Agent v0 Final

**X（Twitter）智能运营 Agent**  
热点监控 + AI 内容生产 + OpenClaw 自动发帖/评论 + 每日复盘

![Status](https://img.shields.io/badge/status-production--ready-green)
![Version](https://img.shields.io/badge/version-v0--final-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## ✨ 核心亮点

- 🔍 **深度情报集成**: 基于 [last30days-skill](https://github.com/mvanhorn/last30days-skill) 的混合检索策略（**不依赖官方 X API**，成本低、数据真实）
- 🎭 **多 Niche 一键切换**: 7 种预置语气（成人 UK、AI 工具、美妆、健身、加密、幽默、自定义）
- 🤖 **多 LLM 路由**: 支持 Claude、Groq、OpenAI 等 7+ 供应商
- 🛡️ **完整防封机制**: 随机延迟 10-40 秒 + 内容变体 + 每日上限
- 📱 **Telegram Bot 驱动**: `/start`, `/set_niche`, `/trends`, `/review` 简单命令
- 📊 **每日智能复盘**: 自动化表现总结与优化建议
- 💾 **Supabase 持久化**: 完整数据记录与历史追溯
- 🐳 **Docker 一键部署**: 生产级开箱即用

---

## 🚀 3 分钟上手

完整指南：**[docs/UP_AND_RUNNING.md](docs/UP_AND_RUNNING.md)**

```bash
# 1. 克隆
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent

# 2. 配置
cp .env.example .env
# 编辑 .env 填入 Telegram Token、Supabase、LLM API Keys

# 3. 安装
pip install -r requirements.txt

# 4. 迁移
supabase db push

# 5. 启动
python main.py

# 6. Telegram 发送 /start 测试
```

**可选增强**: 安装 `last30days` CLI 获得更强情报能力
```bash
pip install last30days
```

---

## 🏗️ 仓库结构

```
x-agent/
├── x-agent/              # 主代码目录
│   ├── main.py           # 入口
│   ├── modules/          # 核心模块（research/scorer/generator/openclaw_bridge）
│   ├── niche_voices/     # 7 种语气模板
│   ├── prompts/          # A/B/C 类 Prompt
│   ├── skills/           # OpenClaw Skill 软链接
│   ├── data/             # 数据缓存
│   └── tests/            # 单元测试
├── docs/                 # 完整文档（上手、部署、贡献指南）
├── archive/              # 历史版本归档
├── README.md             # 主文档
├── docker-compose.yml    # Docker 部署
└── CONTRIBUTING.md       # 贡献指南
```

**开源友好**: MIT 协议，欢迎 PR、Fork、二次开发。

---

## 📚 文档导航

| 文档 | 说明 |
|------|------|
| **[3 分钟上手](docs/UP_AND_RUNNING.md)** | 快速启动清单 |
| **[部署指南](docs/DEPLOYMENT.md)** | 生产环境部署 |
| **[贡献指南](CONTRIBUTING.md)** | 代码规范与 PR 流程 |
| **[版本记录](docs/CHANGELOG.md)** | v0 Final 更新日志 |
| **[截图说明](docs/screenshots/README.md)** | 截图占位与需求 |

---

## 🎯 核心功能

### 1. 多平台情报采集
- 支持 X、Reddit、YouTube、TikTok、HackerNews、Web
- 基于 last30days CLI 的真实数据
- 本地 JSON 缓存，避免重复采集

### 2. 4 维复合评分
- **Relevance** (40%): 文本相似度
- **Velocity** (30%): 24h 互动增速
- **Authority** (15%): 高赞作者/跨平台
- **Convergence** (15%): 多平台同时出现

### 3. AI 内容生成
- **Type A**: 推文/帖子
- **Type B**: 视频脚本
- **Type C**: 评论内容
- 7 种 Niche 语气注入

### 4. OpenClaw 自动化
- 浏览器自动发帖/评论
- 随机延迟 10-40 秒
- 内容变体（emoji/句式）
- 每日上限控制

### 5. Telegram Bot 命令
| 命令 | 说明 |
|------|------|
| `/start` | 欢迎信息与帮助 |
| `/set_niche <niche>` | 切换语气（如 `adult_uk`） |
| `/trends` | 查看当前热点 |
| `/review` | 生成每日复盘 |
| `/status` | 运行状态 |

---

## 🛡️ 防封保护

X-Agent 实现 3 层防护机制：

1. **随机延迟**: 每次操作间隔 10-40 秒随机
2. **内容变体**: 随机 emoji 和句式变化，避免重复检测
3. **每日上限**: 通过 `.env` 的 `MAX_COMMENTS_PER_DAY` 配置（默认 15 条/天）

---

## 🤝 贡献

欢迎贡献！我们需要的帮助：
- 🎭 新增 Niche 语气模板（医疗、教育、科技等）
- 📝 优化 Prompt 质量
- 🌐 扩展数据源（Instagram、Threads 等）
- 🐛 修复 Bug 或新增功能
- 📸 补充实际运行截图

详见 **[CONTRIBUTING.md](CONTRIBUTING.md)**

---

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sheldon010507-collab/x-agent&type=Date)](https://star-history.com/#sheldon010507-collab/x-agent&Date)

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [last30days-skill](https://github.com/mvanhorn/last30days-skill) - 混合检索策略
- [OpenClaw](https://openclaw.ai) - 浏览器自动化框架
- 所有贡献者和支持者！

---

**用 ❤️ 构建 by sheldon010507-collab**

Star ⭐ 支持一下～
