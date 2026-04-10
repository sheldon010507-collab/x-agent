---
name: x-agent
description: "X (Twitter) full-stack automation — multi-platform trend search, AI content generation, auto-posting, DM monitoring, daily reports. Use when user mentions X/Twitter ops, searching trends, writing tweets, checking DMs, or viewing reports."
metadata:
  clawdbot:
    emoji: "🐦"
    requires:
      env: ["X_USERNAME", "X_PASSWORD"]
    primaryEnv: "X_USERNAME"
allowed-tools: Bash(x-agent:*)
---

# X-Agent Skill

X (Twitter) full-stack automation tool with multi-platform trend research, AI content generation, browser-based publishing, DM monitoring, and daily analytics.

**API Base**: `http://localhost:8000` (x-agent REST API running in Docker)

---

## A. Multi-Platform Trend Search

**Trigger**: "search trends", "what's hot", "find trending topics", "搜热点"

```bash
python {baseDir}/scripts/search.py "keyword" [--sources x,tiktok,reddit,hackernews,youtube,web] [--days 7] [--min-score 50]
```

Data sources:
- **X/Twitter**: Playwright real tweet search (requires X_USERNAME/X_PASSWORD)
- **TikTok**: Playwright JS rendering, video titles/likes/authors
- **Reddit**: PRAW API
- **HackerNews**: Official API
- **Google Trends**: pytrends
- **YouTube**: Search page ytInitialData scraping

Returns: Per-platform trend list (title / author / engagement / URL), auto-scored and deduplicated.

---

## B. Multi-Layer Progressive Search

**Trigger**: "first search UK, then search sex, then search telegram"

Flow:
1. Search layer 1: `python {baseDir}/scripts/search.py "UK"`
2. User reviews results, provides next keyword
3. Search layer 2: `python {baseDir}/scripts/search.py "sex" --merge-previous`
4. Repeat up to 5 layers (max)
5. Each layer auto-deduplicates and merges results

Use case: Progressively narrow scope to find precise topics.

---

## C. 4-Dimension Scoring + Risk Assessment

**Trigger**: "score this topic", "rate this trend"

```bash
python {baseDir}/scripts/score.py --topic '{"title":"...", "platform":"x", "likes":500}'
```

Scoring dimensions (total 0-100):
| Dimension | Weight | Description |
|-----------|--------|-------------|
| relevance | 40% | Topic relevance to niche |
| velocity | 30% | 24h growth speed |
| authority | 15% | Source authority (likes/retweets) |
| convergence | 15% | Cross-platform convergence |

Score grades:
- **>= 80 HIGH**: Push immediately
- **60-80 MEDIUM**: Show in summary
- **< 60 LOW**: Store only

Risk scoring (separate dimension):
- **risk >= 80**: Block auto-publish (requires manual review)
- **risk 50-80**: Medium risk, require confirmation
- **risk < 50**: Low risk, safe to auto-publish

---

## D. Content Deduplication (Jaccard Similarity)

Runs automatically before returning search results.

- Algorithm: Jaccard similarity (k=3 shingles, threshold=0.75)
- Flow: Normalize -> Tokenize -> Compute |A∩B|/|A∪B| -> Keep highest-scored item
- LRU cache for performance

---

## E. AI Content Generation

### E1. Tweet Generation (Type A)

**Trigger**: "write a tweet", "generate tweets", "create post"

```bash
python {baseDir}/scripts/generate.py "topic" --type tweet --niche ai_tools [--summary "background info"]
```

Returns 3 tweets with different angles:
1. **Hot Take** - Bold, contrarian opinion
2. **Data/Research** - Data-driven insight
3. **Interactive Poll** - Engagement question

### E2. Video Script Generation (Type B)

**Trigger**: "create video script", "write a script"

```bash
python {baseDir}/scripts/generate.py "topic" --type video --niche crypto
```

Returns: Complete 30s video script (hook 0-5s / body 5-20s / CTA 20-30s), caption, hashtags, posting time suggestion.

### E3. Smart Comment Generation (Type C)

**Trigger**: "generate a comment", "reply to this tweet"

```bash
python {baseDir}/scripts/generate.py "tweet content" --type comment --niche humor
```

Returns 3 comment options. Style traits:
- **conversational**: Casual, friendly
- **analytical**: Data-focused, insightful
- **supportive**: Encouraging, positive
- **curious**: Question-based, engaging

### E4. Niche Voice System

7 content niches, each with distinct tone injection:

| Niche | Voice Style |
|-------|-------------|
| general | Professional, balanced |
| ai_tools | Technical, cutting-edge, expert |
| crypto | Analytical, cautious, data-driven |
| beauty | Warm, encouraging, emoji-rich |
| fitness | Motivational, energetic, practical |
| humor | Playful, witty, meme-aware |
| adult | Adult content (adult_uk variant: British slang) |

Voice files: `x-agent/niche_voices/*.txt`

### E5. AI Trend Analysis Report

**Trigger**: "analyze this trend", "give me a report on..."

```bash
python {baseDir}/scripts/analyze.py "keyword" [--sources x,tiktok,reddit]
```

Flow: Search data -> LLM generates Markdown analysis report
Report sections: Trend overview / Popularity ranking / Cross-platform convergence / Risk warnings / Recommendations

---

## F. X Platform Automation (Playwright Browser)

All operations have anti-ban mechanisms: random delays + content variants + daily limits.

### F1. Post Tweet

```bash
python {baseDir}/scripts/post.py --content "tweet content" [--no-variant]
```

- Anti-ban: Random delay 10-40s, auto emoji/phrase variants
- Daily limit: 10 posts max

### F2. Comment on Tweet

```bash
python {baseDir}/scripts/comment.py --url "https://x.com/user/status/123" --content "comment text"
```

- Daily limit: 15 comments max

### F3. Like Tweet

```bash
python {baseDir}/scripts/like.py --url "https://x.com/user/status/123"
```

- Daily limit: 30 likes max
- Delay: 5-15s (shorter)

### F4. Retweet

```bash
python {baseDir}/scripts/retweet.py --url "https://x.com/user/status/123" [--comment "quote text"]
```

- Daily limit: 10 retweets max

---

## G. X DM Monitoring (Fingerprint Browser)

**Trigger**: "check DMs", "view messages", "monitor DMs"

### G1. View DM List

```bash
python {baseDir}/scripts/dms.py
```

Features:
- Fingerprint browser spoofing (hide webdriver, fake plugins/languages)
- Session cookie persistence (20h TTL, avoid repeated logins)
- Human-like random delays

Returns: Sender / message preview / unread status / timestamp / conversation link

### G2. Background Real-time Monitoring

```bash
python {baseDir}/scripts/dms.py --monitor --interval 300
```

Features:
- Check every 5 minutes (±30s jitter for anti-detection)
- Auto-notify on new messages
- Seen records persisted to `data/dm_seen.json`

---

## H. Daily Operations Rhythm

Teach the Agent to self-organize:

| Schedule | Action |
|----------|--------|
| Every 2 hours | Auto-search trends -> Score -> Dedup -> Store high-score topics |
| Daily 21:00 UK | Generate daily report -> Push to user |
| On demand | User-triggered search / generate / publish / DMs |
| Continuous | DM monitoring (every 5 min) |

---

## I. Daily Operations Report

**Trigger**: "show daily report", "today's stats"

```bash
python {baseDir}/scripts/report.py [--date 2026-04-10]
```

Data: Posts count / Comments count / Likes count / Retweets count / Top engagement
Source: SQLite local DB or Supabase cloud

---

## J. Multi-LLM Provider Support

```bash
python {baseDir}/scripts/llm_status.py
```

Supported providers (priority order):
1. **Anthropic** (claude-3-5-sonnet) - Recommended
2. **OpenAI** (gpt-4o)
3. **Groq** (llama-3.3-70b) - Free tier
4. **Gemini** (gemini-2.0-flash)
5. **OpenRouter** (aggregated)
6. **NVIDIA NIM**
7. **Ollama** (local, always available)

Routing: Based on `LLM_PROVIDER` env var. Auto-fallback on failure.

---

## K. Risk Control Rules (Agent MUST Follow)

| Action | Daily Limit | Delay |
|--------|-------------|-------|
| Post | 10 max | 10-40s random |
| Comment | 15 max | 10-40s random |
| Like | 30 max | 5-15s |
| Retweet | 10 max | 10-40s random |

Additional rules:
- **Content variants**: Auto-add random emoji + phrase (anti-duplicate detection)
- **risk_score >= 80**: BLOCK auto-publish (must have manual review)
- **risk_score 50-80**: Show risk warning, require confirmation
- **Fingerprint browser**: All Playwright operations inject stealth JS
- **Session**: Cookie persistence, 20h auto-refresh

---

## L. Configuration Validation

```bash
python {baseDir}/scripts/validate_config.py
```

Checks: Telegram token / LLM API key / Supabase / Reddit / X credentials
Output: Configuration status report (what's configured, what's missing)

---

## Environment Variables

Required:
- `X_USERNAME` - X (Twitter) login email
- `X_PASSWORD` - X (Twitter) password

Optional:
- `ANTHROPIC_API_KEY` - Anthropic API key (or other LLM provider)
- `SUPABASE_URL` / `SUPABASE_KEY` - Database
- `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` - Reddit API
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` - Notifications
