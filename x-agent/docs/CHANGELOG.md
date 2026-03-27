# CHANGELOG.md - 版本变更记录

所有重要变更将记录在此文件中。

---

## [v0 Final] - 2026-03-27

### ✨ 新增
- **last30days 深度集成**: `research.py` 完整集成 last30days CLI，支持多平台 30 天真实数据
- **Fallback 机制**: 未安装 last30days CLI 时自动降级到传统趋势源
- **Logging 系统**: `main.py` 添加控制台 + 文件双输出日志
- **防封强化**: 
  - 随机延迟 10-40 秒
  - 内容变体（emoji/句式随机）
  - 每日上限配置 (`MAX_COMMENTS_PER_DAY`)
- **文档系统**:
  - 中英双语 README.md
  - 3 分钟上手指南 `UP_AND_RUNNING.md`
  - 贡献指南 `CONTRIBUTING.md`
  - 部署指南 `DEPLOYMENT.md`

### 🔧 优化
- **仓库结构清理**: 
  - 旧版本归档至 `archive/`
  - `x-agent/` 作为唯一主目录
- **配置优化**: `.env.example` 包含完整配置项和说明
- **测试覆盖**: 完善 `tests/` 目录结构

### 📦 工程化
- 添加 `requirements.txt` 依赖清单
- 添加 `docker-compose.yml` 一键部署配置
- 添加 `.dockerignore` 文件
- 统一日志格式和路径

### 🐛 修复
- 修复 last30days 调用超时问题（延长至 180 秒）
- 修复 JSON 缓存路径问题
- 修复 Telegram 命令响应延迟

---

## [v3.0] - 2026-03-25

### ✨ 新增
- 多 Niche 支持（7 种预置语气）
- 多 LLM 路由（Claude/Groq/OpenAI）
- Telegram Bot 完整命令集
- Supabase 数据库支持
- OpenClaw 浏览器自动化

### 🔧 优化
- 4 维复合评分系统
- A/B 测试内容生成
- 每日复盘报告

---

## [v2.0] - 2026-03-20

### ✨ 新增
- OpenClaw 基础集成
- 基础热点监控
- 简单内容生成

---

## [v1.0] - 2026-03-15

### ✨ 新增
- 初始版本发布
- 基础 X 平台监控
- 简单发帖功能

---

## 版本说明

- **v0 Final**: 生产级优化版本，结构清晰、文档完整、可直接开源
- **v3.0**: 功能完整版，多 Niche 多 LLM 支持
- **v2.0**: OpenClaw 集成版本
- **v1.0**: 初始版本

---

**计划中**:
- [ ] 支持更多数据源（Instagram, Threads）
- [ ] 多语言内容生成
- [ ] 高级复盘分析（周/月报）
- [ ] Web 管理界面
- [ ] 插件系统
