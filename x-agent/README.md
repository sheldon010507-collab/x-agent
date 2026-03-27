# X-Agent v0

**X (Twitter) Intelligent Operations Agent**  
Hotspot Monitoring + AI Content Generation + OpenClaw Auto-Posting/Commenting + Daily Review

![Status](https://img.shields.io/badge/status-production--ready-green)
![Version](https://img.shields.io/badge/version-v0--final-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 📸 Screenshots

| Telegram Bot Interface | Auto-Generated Post | Daily Review Report |
|------------------------|---------------------|---------------------|
| ![Bot Interface](docs/screenshots/bot_interface.png) | ![Post Example](docs/screenshots/post_example.png) | ![Daily Report](docs/screenshots/daily_report.png) |

---

## ✨ Features

- **Multi-Platform Intelligence**: Aggregates trends from X, Reddit, YouTube, TikTok, HackerNews (powered by [last30days-skill](https://github.com/mvanhorn/last30days-skill))
- **AI Content Generation**: Generates posts/comments with 7+ preset tones (Adult UK, AI Tools, Beauty, Fitness, Crypto, Humor, Custom)
- **OpenClaw Automation**: Browser-based posting/commenting with anti-ban protection (random delays, content variation, daily limits)
- **Multi-LLM Routing**: Supports Claude, Groq, OpenAI, and more
- **Telegram Bot Control**: Simple commands (`/start`, `/set_niche`, `/trends`, `/review`)
- **Daily Review Reports**: Automated performance summaries

---

## 🚀 Quick Start (3 Minutes)

1. **Clone & Enter**:
   ```bash
   git clone https://github.com/sheldon010507-collab/x-agent.git
   cd x-agent/x-agent
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your keys
   ```

3. **Required Keys** (fill in `.env`):
   - `TELEGRAM_BOT_TOKEN`: From [@BotFather](https://t.me/botfather)
   - `TELEGRAM_CHAT_ID`: Your Telegram chat ID
   - `SUPABASE_URL` & `SUPABASE_KEY`: [Supabase](https://supabase.com) credentials
   - LLM API keys (at least one)

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run Database Migrations**:
   ```bash
   supabase db push
   ```

6. **Start the Agent**:
   ```bash
   python main.py
   ```

7. **Test in Telegram**: Send `/start` to your bot

8. **(Optional) Install last30days CLI** for enhanced intelligence:
   ```bash
   pip install last30days
   ```

---

## 🎯 Supported Niches & Tones

| Niche | Description | Command |
|-------|-------------|---------|
| Adult UK | UK-focused adult industry content | `/set_niche adult_uk` |
| AI Tools | AI tool reviews and tutorials | `/set_niche ai_tools` |
| Beauty | Beauty product reviews and tips | `/set_niche beauty` |
| Fitness | Fitness tips and motivation | `/set_niche fitness` |
| Crypto | Cryptocurrency news and analysis | `/set_niche crypto` |
| Humor | Funny, engaging content | `/set_niche humor` |
| Custom | Your own custom tone | `/set_niche custom` |

---

## 🏗️ Architecture

```
x-agent/
├── main.py              # Entry point
├── config.py            # Configuration loader
├── modules/
│   ├── research.py      # Trend research (last30days integration)
│   ├── scorer.py        # 4-dimension scoring (Relevance, Velocity, Authority, Convergence)
│   ├── generator.py     # AI content generation
│   ├── llm_router.py    # Multi-LLM routing
│   ├── openclaw_bridge.py # OpenClaw automation with anti-ban rules
│   └── bot.py           # Telegram bot commands
├── prompts/             # A/B test prompts
├── niche_voices/        # Niche-specific tone templates
├── skills/              # OpenClaw skills
├── migrations/          # Supabase schema
├── data/                # Local cache and logs
└── tests/               # Unit tests
```

---

## 📚 Documentation

- **[3-Minute Quick Start](docs/UP_AND_RUNNING.md)** - Complete setup checklist
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Changelog](docs/CHANGELOG.md)** - Version history

---

## 🛡️ Anti-Ban Protection

X-Agent implements 3-layer protection:

1. **Random Delays**: 10-40 seconds between actions
2. **Content Variation**: Random emoji and sentence structure changes
3. **Daily Limits**: Configurable via `MAX_COMMENTS_PER_DAY` in `.env`

---

## 🤝 Contributing

Contributions welcome! Areas we need help:

- New niche tones (`niche_voices/`)
- Prompt optimization (`prompts/`)
- New platform support (extend `research.py` sources)
- Bug fixes and feature additions

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=sheldon010507-collab/x-agent&type=Date)](https://star-history.com/#sheldon010507-collab/x-agent&Date)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [last30days-skill](https://github.com/mvanhorn/last30days-skill) - Mixed retrieval strategy
- [OpenClaw](https://openclaw.ai) - Browser automation framework
- All contributors and supporters!

---

**Made with ❤️ by sheldon010507-collab**
