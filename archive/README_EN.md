# X-Agent — Intelligent X Platform Content Operations Assistant

A Telegram-driven trend monitoring + content generation + daily review system for English-market X accounts (0-1k growth phase).

## Features

- 🔥 **Trend Collection**: Reddit + Google Trends + X Trending, auto-collects every 2 hours
- 📊 **Smart Scoring**: 50-keyword library, automatic high-value topic filtering
- ✍️ **Content Generation**: Type A (direct tweets) + Type B (video scripts)
- 📈 **Daily Review**: Auto-generates operations report at 21:00 UK time
- 🤖 **Telegram-Driven**: All operations via Bot commands

## Tech Stack

- Python 3.11+
- python-telegram-bot 20.7
- Multi-LLM Support (Anthropic Claude / OpenAI / Groq / Gemini / OpenRouter / NVIDIA NIM / Ollama)
- Supabase (PostgreSQL)
- PRAW (Reddit API)
- pytrends (Google Trends)
- APScheduler + PM2

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Initialize database
# Run database_schema.sql in Supabase

# 5. Start
python main.py
```

## Project Structure

```
x-agent/
├── main.py              # Main entry point
├── config.py            # Configuration loader
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── database_schema.sql  # Supabase schema
├── modules/
│   ├── database.py      # Supabase operations
│   ├── trends.py        # Data collection (Reddit/Google/X)
│   ├── scorer.py        # Trend scoring logic
│   ├── generator.py     # Claude content generation
│   ├── bot.py           # Telegram Bot
│   └── scheduler.py     # Scheduled tasks
├── prompts/
│   ├── type_a.txt       # Type A content prompt
│   ├── type_b.txt       # Type B script prompt
│   └── review.txt       # Daily review prompt
├── niche_voices/        # Niche-specific tone files
└── skills/              # OpenClaw agent skills
    ├── git/             # Git operations
    ├── github/          # GitHub integration
    ├── security-audit/  # Security auditing
    └── ...              # Code review tools
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Today's trends overview + quick menu |
| `/set_niche` | Switch content niche |
| `/trends` | Current trends (sorted by score) |
| `/create` | Create content (Type A/B) |
| `/log` | Log today's posting data |
| `/report` | View review report |
| `/queue` | View draft queue |
| `/settings` | Automation settings panel |
| `/llm` | Switch LLM provider |

## Database Tables

- `trends` — Trend records
- `content_queue` — Content drafts
- `daily_log` — Daily data logs
- `strategy` — Strategy versions
- `automation_settings` — Automation toggles

## Agent Skills Included

This repo includes Reviewer agent's code review skills:
- **git** — Git operations and workflows
- **github** — GitHub CLI integration
- **security-audit-toolkit** — Security vulnerability scanning
- **clean-code-review** — Code quality standards
- **e2e-testing-patterns** — Playwright/Cypress testing patterns

## Development Progress

- [x] Project structure
- [x] Database module (database.py)
- [x] Scoring module (scorer.py)
- [x] Scheduler module (scheduler.py)
- [x] Content generation module (generator.py)
- [x] Prompt templates
- [x] Bot skeleton (bot.py)
- [x] Agent skills integration
- [ ] Data collection module (trends.py) — Connection
- [ ] Bot interaction polish — Frontend

## License

MIT
