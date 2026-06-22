# Ponytail Plan: x-agent + last30days-skill 优化

## 背景
last30days-skill 是 44k star 的 Reddit 研究工具，有实体解析、多源聚合、HTML 报告输出。
x-agent 已有：Reddit keyless 三层管线、Playwright 爬虫、X DM 监控、Dashboard、SQLite、Telegram Bot。
目标：取其精华，不引入新依赖，砍死代码，Playwright 统一，Dashboard 做账号监控看板。

---

## Phase 1: 砍死代码（ponytail delete）

先清掉 2800+ 行死代码，减少认知负担，再谈优化。

```
delete  bot.py (752L) + bot_v0_final.py (380L) 根目录两个死文件，main.py 从未引用
delete  modules/bot.py (505L) 被 modules/bot_v0_final.py 取代
delete  modules/config_validator.py (354L) 无人 import，config.py 自己有 _validate()
delete  modules/config_resolver.py (124L) 无人 import，dotenv 逻辑与 config.py 重复
delete  modules/quality_telemetry.py (183L) telemetry 全局对象无人读写
delete  modules/intent_classifier.py (148L) classify() 无人调用
delete  modules/bot_api_commands.py (243L) 一层无意义包装，直接传 CommandHandler
shrink  modules/scorer.py 删 v2 方法 (~150L 死代码) + WEIGHTS_BASE/ENHANCED 常量
delete  modules/__init__.py (~50L) lazy __getattr__ 导出 4 个不存在的符号，直接抛 AttributeError
delete  根目录 _fix_indent.py (42L) 一次性脚本
```

依赖清理：
```
delete  requirements.txt: cryptography (540KB，读了 encryption_key env var 但从未用)
yagni  praw + pytrends — trends.py 里 try/except 静默吞掉，永远回退空列表
```

验证方法：删完后 `python -c "import x_agent"` 不报错 + 跑 test_integration.py。

---

## Phase 2: Playwright 统一（核心）

**问题**：`reddit_playwright.py` 的 `RedditPlaywrightCrawler` 和 `dashboard/dm_monitor.py` 的 `XDMMonitor`/`RedditDMMonitor` 各自重复了：
- chromium.launch(args=...) 参数
- stealth JS 注入（三个文件各有一份几乎一样的）
- cookie 加载/持久化
- context 创建（viewport, locale, timezone, user_agent）

**方案**：抽一个 `modules/browser_pool.py`，单例管理 browser + context pool。

```python
# 伪代码
class BrowserPool:
    _instance = None
    def __init__(self):
        self._playwright = None
        self._contexts: dict[account_id, BrowserContext] = {}

    async def get_context(self, account: RedditAccount) -> BrowserContext:
        if account.id in self._contexts:
            return self._contexts[account.id]
        ctx = await self._browser.new_context(**BASE_CTX_KWARGS)
        await ctx.add_init_script(STEALTH_JS)
        if Path(account.cookies_file).exists():
            await ctx.add_cookies(json.loads(Path(account.cookies_file).read_text()))
        self._contexts[account.id] = ctx
        return ctx

    async def rotate_account(self, old_id, new_account):
        old = self._contexts.pop(old_id, None)
        if old: await old.close()
        return await self.get_context(new_account)

    async def shutdown(self):
        for ctx in self._contexts.values():
            await ctx.close()
        if self._browser: await self._browser.close()
```

收益：
- STEALTH_JS 只定义一次（3处合并为1）
- `RedditPlaywrightCrawler` 不再持有 `_playwright/_browser/_context/_page`，从 pool 拿
- `XDMMonitor` / `RedditDMMonitor` 也从 pool 拿 context
- 多账号轮换变成 pool.rotate_account()，不要每个类各自实现

---

## Phase 3: Dashboard 看板增强

**现状**：Dashboard 已有账号卡片、活动图表、告警、DM 面板。
**缺口**：发帖记录只存在 runs 表，没有按账号聚合的"今日发帖列表"视图。

新增一个 `PostFeedPanel`（前端 tab + 后端 API）：

```
后端：
  GET /api/posts?account_id=&platform=&days=7&limit=50
  从 runs 表 + findings 表聚合，返回每条帖子：
  { id, account_id, platform, title, url, posted_at, engagement_score, status }

前端：
  new tab "Posts" → 表格 + 平台颜色 badge + 按账号筛选
  每条帖子可点击跳转到原帖链接
```

**账号健康看板增强**：
- 每个账号卡片加 sparkline（7天发帖趋势）
- 限流预警 + 冷却时间倒计时
- Playwright 爬虫的 `get_account_status()` 已在 reddit_playwright.py 实现，Dashboard 后台任务调用它填充真实 karma/请求数，替代 launch.py 里的 random 假数据

---

## Phase 4: 借鉴 last30days-skill 的精华

**只取三个点，不做全量搬运：**

### 4a. 实体预解析（轻量版）
last30days 的 Step 0 会把人名→X handle、产品→subreddit 做映射。
x-agent 已有 `_NICHE_SUBS` 字典，直接扩展它：

```python
# modules/research.py 里扩展
_NICHE_SUBS = {
    "ai_tools": ["artificial", "MachineLearning", "OpenAI", "ChatGPT"],
    # ... 已有
}

# 新增：人名 → X handle 映射 (用于精准搜索)
_PERSON_X_HANDLES = {
    # "openai": ["sama", "gdb", "sundarpichai"],
}

# 新增：产品 → 官方来源映射
_PRODUCT_SOURCES = {
    # "claude": {"x": ["anthropic"], "subreddits": ["ClaudeAI", "anthropic"]},
}
```

不要做完整的 LLM 解析 pipeline，就一个 dict lookup，YAGNI。

### 4b. 多源结果聚类（现有基础上加 dedup）
last30days 的 Step 2 会把同一事件的多源结果合并。
x-agent 已有 `ContentDeduplicator`（deduplicator.py），但它是基于标题 3-gram 的。
优化：在 Reddit → X → HN 结果返回后，按 URL domain + 关键词 overlap 做二级聚类。

```python
# 在 research.py 的 fetch() 返回前加一步
def _cluster_cross_source(self, results: list[dict]) -> list[dict]:
    """同一事件的 Reddit 帖 + X 帖合并为一个 cluster"""
    seen_domains = {}
    for r in results:
        domain = urlparse(r.get("url","")).netloc
        key = r.get("_topic_key", "")
        seen_domains.setdefault(key, []).append(r)
    # ... 合并同一 key 下的多平台结果为 cluster
```

### 4c. 定时复盘推送（watchlist 模式）
last30days 有 `watchlist.py` + `briefing.py` 做每日摘要。
x-agent 已有 `scheduler.py` + Dashboard 的 WebSocket 推送。
最小实现：每天 21:00 跑一次 research，把 Top-5 新帖推送到 Telegram Bot。

```python
# 在 scheduler.py 的 loop 里加一条
if hour == 21:
    results = await researcher.fetch_all_platforms()
    top5 = sorted(results, key=score, reverse=True)[:5]
    await telegram_bot.send_daily_brief(top5)
```

---

## 执行顺序（不跳步）

```
1. 砍死代码 (Phase 1) → 验证 import 不破
2. BrowserPool 统一 (Phase 2) → Playwright 模块改 3 个文件
3. Dashboard PostFeed + 真实状态 (Phase 3) → 2 个新 API + 1 个新 tab
4. 实体映射 + 聚类 + 定时推送 (Phase 4) → 小范围改动，不碰核心管线
```

**不做的事**：
- 不搬 last30days 的 HTML brief 生成（已有的 Dashboard 更实时）
- 不做完整的 entity resolution LLM pipeline（现在用 dict lookup 够用）
- 不加 TikTok/Instagram/Bluesky 采集（你现在只用 Reddit+X）
- 不搬 ScrapeCreators API（付费依赖）

**net: -2800 行死代码, +1 BrowserPool 统一层 (~150L), +Dashboard 发帖面板 (~200L), +实体映射/聚类/推送 (~200L)**
