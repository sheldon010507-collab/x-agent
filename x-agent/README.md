# X-Agent

X-Agent is a research-to-publishing assistant for social media operators. It collects signals from multiple public sources, deduplicates and scores them, turns them into marketing insights, and keeps publishing behind a manual approval workflow.

The product goal is simple: help one person monitor more platforms, find better content angles, and draft safer posts without handing full control to automation.

## What It Does

- Multi-source research: Reddit, X/Twitter, YouTube, Hacker News, Google Trends and web-style trend sources are supported in the current codebase.
- Keyless Reddit collection: includes a last30days-inspired Reddit pipeline with HTTP/RSS fallbacks and browser fallback support.
- Evidence-first summaries: stores citations, source URLs, engagement signals and platform coverage with each research result.
- Marketing analysis: converts raw research into pain points, content angles, lead magnets, free-tool ideas, prospecting signals and sales talking points.
- Draft generation: creates X/Twitter post drafts, short video scripts and reply drafts using the configured LLM router.
- Manual approval: generated content is saved as draft first and requires human confirmation before publishing.
- OpenClaw integration: can hand approved actions to OpenClaw for browser-based social automation.
- Dashboard/API mode: includes FastAPI endpoints and a lightweight dashboard for accounts, runs, findings and health.

## Why It Exists

Social research gets noisy fast. A single trend can appear across Reddit threads, YouTube videos, X posts, prediction markets and news pages. X-Agent is built to reduce that noise into a usable publishing brief:

1. Search across selected platforms.
2. Deduplicate similar findings.
3. Score relevance, velocity, authority and risk.
4. Extract marketing opportunities.
5. Generate draft content.
6. Require human review before anything is posted.

## Current Architecture

```text
Researcher
  Collects platform data, citations and metrics.

MarketingAnalyzer
  Turns evidence into audience, content, growth and sales insights.

ContentGenerator
  Uses the LLM router to generate posts, scripts and comments.

Telegram Bot / API / Dashboard
  Exposes the workflow for operators.

OpenClaw Bridge
  Executes approved browser actions when configured.
```

The system intentionally keeps platforms as connectors rather than separate agents. This keeps concurrency lower, reduces account risk and makes failures easier to debug.

## Platform Status

| Platform | Status | Notes |
| --- | --- | --- |
| Reddit | Active | Keyless pipeline plus optional PRAW/browser fallback |
| X/Twitter | Active | Static trend source plus optional browser automation |
| YouTube | Active | Trending/search-style scraping support |
| Web/Google Trends | Active | Trend source support |
| Hacker News | Active | Official Firebase API |
| TikTok | Experimental | Static/browser collection path exists |
| Instagram | Planned | Should use official API only |
| Threads | Planned | Connector not finalized |
| Polymarket | Planned | Connector not finalized |
| Facebook | Out of scope | Intentionally removed |

## Safety Model

X-Agent is designed for supervised operation.

- No fully automatic publishing path is required.
- Drafts are reviewed before posting.
- Risk score is included in research and generation flows.
- Account separation is recommended: use dedicated research accounts and separate publishing accounts.
- Platform terms, rate limits and account safety remain the operator's responsibility.

This project is for research, workflow automation and operator assistance. Automated platform activity may violate platform terms of service. Use carefully.

## Quick Start

```bash
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

For Docker:

```bash
cd x-agent
docker compose up -d x-agent-api
```

API health check:

```bash
curl http://localhost:8000/health
```

## Core Commands

Run tests:

```bash
cd x-agent
python -m pytest -q
```

Run API:

```bash
cd x-agent
uvicorn api:app --host 0.0.0.0 --port 8000
```

Run MCP server:

```bash
cd x-agent
python mcp_server.py
```

## Repository Layout

```text
x-agent/
  api.py                         FastAPI service
  main.py                        app entrypoint
  mcp_server.py                  MCP integration
  modules/
    research.py                  multi-platform research
    marketing_analysis.py        marketing and growth insight layer
    generator.py                 post/script/comment generation
    database.py                  local persistence
    openclaw_bridge.py           OpenClaw automation bridge
  dashboard/                     operator dashboard
  tests/                         automated test suite
  docs/                          deployment and risk docs
```

## Development Status

Recent work focused on simplifying the repository and productizing the workflow:

- removed a duplicated nested project tree
- added marketing analysis between research and publishing
- kept platform collectors inside the research layer instead of creating more agents
- kept publishing human-approved
- verified the suite with `160 passed, 1 skipped`

## License

MIT
