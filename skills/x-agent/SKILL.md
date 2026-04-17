---
name: x-agent
description: X/Twitter trend research, AI content generation, and automated social actions across X, TikTok, YouTube, Reddit, Hacker News, and Google Trends. Use this skill whenever the user asks to research trends/hot topics, search a niche, find what's trending in a country/topic, generate tweets or video scripts or comments, post/comment/like/retweet on social media, or run any X/Twitter automation. Trigger keywords (English & Chinese): "trend", "trending", "hot topic", "research", "find what people say about", "scrape", "post a tweet", "comment on", "like", "retweet", "热点", "趋势", "查一下", "看看", "搜索", "发推", "发帖", "评论", "点赞", "转发", "推特", "X", "抖音", "TikTok", "YouTube".
metadata: {"clawdbot":{"emoji":"🤖","requires":{"anyBins":["python3","python"]}}}
---

# X-Agent — Browser Automation for X/Twitter & Social Platforms

> **For OpenClaw orchestration**: This skill is a CLI toolset. The user talks naturally in Telegram; you (OpenClaw) translate intent to one or more `x-agent` shell commands and stream JSON output back. See **§ Natural-Language Recipes** below for the exact mapping.

## Setup (run once)

```bash
cd ~/.openclaw/workspace/skills/x-agent
pip install -e .
playwright install chromium
export ANTHROPIC_API_KEY="sk-ant-..."

# Login per platform (opens visible browser, user logs in manually, press ENTER when done)
x-agent login --platform x
x-agent login --platform tiktok    # optional
x-agent login --platform youtube   # optional
```

---

## § Natural-Language Recipes (CRITICAL for OpenClaw)

When the user sends a Telegram message, match the intent and run the matching command(s). Always stream JSON output back; format it nicely for Telegram.

### A. Trend research

| User says (any language) | Run |
|---|---|
| "帮我查下英国成人用品的趋势" / "Find UK adult product trends" | `x-agent trends --query "uk adult" --niche adult` |
| "看看 AI 工具最近在火什么" / "What's hot in AI tools" | `x-agent trends --niche ai_tools` |
| "搜索 GPT-5 的讨论" | `x-agent trends --query "GPT-5"` |
| "查英国健身博主早晨routine" | `x-agent trends --query "uk fitness" --refine "morning routine"` |
| "在 Reddit 和 X 上看 crypto 热点" | `x-agent trends --niche crypto --sources x,reddit` |
| "刚刚最爆的 AI 帖子" / "What just blew up in AI" | `x-agent trends --niche ai_tools --rank-by velocity` |
| "在已有结果里再筛 Sora 相关的" | `x-agent search --query "Sora"` |
| "再加个 'video' 关键词缩小" | `x-agent search --query "Sora" --refine "video"` |

**How to read the output for the user**:
- `top_posts[]` — actual hottest posts. Each has `engagement` (weighted score) and `velocity` (engagement per hour).
- `summary` — one-line Chinese/English summary you can show directly.
- `filter_traces` — shows how many posts each refine layer kept (useful when user asks "怎么过滤的").

### B. Content generation

| User says | Run |
|---|---|
| "针对最热的话题给我写 3 条推文" | First `x-agent trends ...`, take `top_posts[0].title`, then `x-agent create --type a --topic "<that title>" --niche <niche>` |
| "写个 30 秒的视频脚本" | `x-agent create --type b --topic "<topic>" --niche <niche>` |
| "给这个推文写 3 条评论" | `x-agent create --type c --topic "<original tweet text>"` |
| "用加密货币的语气" | Add `--niche crypto` |
| Available niches | `ai_tools`, `crypto`, `fitness`, `beauty`, `humor`, `adult`, `general`, `custom` |

### C. Social actions (require login first)

| User says | Run |
|---|---|
| "帮我发出去" (after generation) | `x-agent post --platform x --content "<the generated tweet>"` |
| "在这条下面评论 'Nice take'" | `x-agent comment --platform x --url <url> --content "Nice take"` |
| "点个赞" | `x-agent like --platform x --url <url>` |
| "转发并加个评论 'must-read'" | `x-agent retweet --url <url> --quote "must-read"` |
| "关注这个 TikTok 博主" | `x-agent follow --platform tiktok --url <profile>` |
| "订阅这个 YouTube 频道" | `x-agent subscribe --url <channel>` |

### D. Status / management

| User says | Run |
|---|---|
| "都登录了哪些平台" / "show sessions" | `x-agent sessions` |
| "今天还能发几条" / "check daily limits" | `x-agent limits` |
| "今天做了什么" / "daily report" | `x-agent report` |
| "登出 X" | `x-agent logout --platform x` |
| "整体状态" | `x-agent status` |

### E. Multi-step workflows (chain commands)

**Common pipeline**: research → pick top → generate → confirm with user → post.

```bash
# Step 1: research (OpenClaw runs this)
RES=$(x-agent trends --query "uk adult")

# Step 2: extract top topic, generate content (OpenClaw uses LLM to pick topic from RES)
CONTENT=$(x-agent create --type a --topic "<extracted topic>" --niche adult)

# Step 3: confirm with user in Telegram, then post
# (OpenClaw shows CONTENT to user, waits for "yes/发出去")
x-agent post --platform x --content "<extracted tweet from CONTENT.raw.tweets[0].content>"
```

**Important**: Always show generated content to the user and wait for confirmation BEFORE running `post`/`comment`/`like` — these actions are irreversible and rate-limited.

---

## § Command Reference

### Research
```
x-agent trends [--niche N] [--query Q] [--refine R ...] [--sources S]
               [--days D] [--limit L] [--rank-by engagement|velocity|recent]
               [--headed] [--full]
x-agent search [--query Q] [--refine R ...] [--niche N] [--limit L]
```

- `--query` overrides niche default keyword. If both omitted, uses general default.
- `--refine` can repeat; each layer narrows by matching **title + body + author + tags**.
- `--rank-by velocity` surfaces breakout posts (engagement per hour); `engagement` is total weighted互动.
- Default summary output; add `--full` for raw JSON dump.

### Generation
```
x-agent create --type {a|b|c} --topic "..." [--niche N]
x-agent score --input file.json
```
- Type **a**: 3 tweet variants (Hot take / Data / Poll)
- Type **b**: 30-sec video script (Hook / Body / CTA)
- Type **c**: 3 smart comment options

### Sessions
```
x-agent login    --platform {x|tiktok|youtube|reddit|hackernews|google_trends}
x-agent sessions
x-agent logout   --platform <p>
```

### Actions (require login)
```
x-agent post     --platform x --content "..."
x-agent comment  --platform <p> --url <url> --content "..."
x-agent like     --platform <p> --url <url>
x-agent retweet  --url <url> [--quote "..."]
x-agent follow   --platform tiktok --url <profile>
x-agent subscribe --url <channel>
x-agent limits
```

### Reports
```
x-agent status
x-agent report [--date YYYY-MM-DD]
```

---

## § How Trends Are Judged

Posts are ranked by **real engagement** scraped from each platform (not by post count):

| Platform | Engagement formula |
|---|---|
| X / Twitter | `likes×1 + retweets×2 + replies×3 + views×0.01` |
| Reddit | `score×1 + num_comments×2` |
| Hacker News | `score×1 + descendants×2` |
| YouTube | `views×0.01 + likes×1` |
| TikTok | `engagement_count×0.01` |

Each post also gets a `velocity_per_hour = engagement / hours_since_posted`. High velocity = post is "blowing up right now". Use `--rank-by velocity` to surface breakouts the user wouldn't see in normal hot/top sorts.

The trend-level (multi-platform) score combines:
- relevance (25%)
- velocity (30%)
- authority (15%)
- platform convergence (15%)
- engagement (10%)
- temporal decay (2.5%)
- platform diversity (2.5%)

Output `score_level`: `HIGH (≥80)` / `MEDIUM (60-79)` / `LOW (<60)`
Output `action`: `PUSH_NOW` / `ADD_TO_DIGEST` / `STORE_ONLY` / `DISCARD`

---

## § Default Daily Action Limits

| Platform | Post | Comment | Like | Other |
|---|---|---|---|---|
| X | 5 | 15 | 30 | retweet: 10 |
| TikTok | — | 10 | 30 | follow: 10 |
| YouTube | — | 10 | 30 | subscribe: 5 |

Action calls auto-fail when daily limit reached (returns `success: false` with limit info). Random 10-40s delays between action steps; stealth fingerprinting on every browser context.

---

## § Storage

- `~/.x-agent/sessions/{platform}_auth.json` — login cookies (sensitive, do not share)
- `~/.x-agent/data/trends.json` — collected trends history
- `~/.x-agent/data/content.json` — generated content history
- `~/.x-agent/data/reports.json` — daily reports
- `~/.x-agent/data/action_counters.json` — daily action quotas

---

## § Environment Variables

| Variable | Required | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` (or any LLM key) | yes (one) | — |
| `OPENAI_API_KEY` / `GROQ_API_KEY` / `OPENROUTER_API_KEY` | optional alt | — |
| `LLM_PROVIDER` | optional | `anthropic` |
| `LLM_MODEL` | optional | `claude-sonnet-4-20250514` |
| `X_AGENT_NICHE` | optional | `general` |
| `X_AGENT_DATA_DIR` | optional | `~/.x-agent/data` |

---

## § Risk Disclaimer

Browser automation on social platforms may violate ToS and lead to account bans. Built-in safety (stealth, daily limits, random delays) reduces but does NOT eliminate risk. **Use test accounts first.** Never run actions for the user without explicit confirmation in Telegram.
