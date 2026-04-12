# Contributing to X-Agent

Thank you for your interest in contributing to X-Agent!

## Development Setup

```bash
# Clone and setup
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent/x-agent
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

## How to Contribute

### Report Bugs

1. Check existing issues first
2. Create a new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs/screenshots if applicable

### Submit Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `python -m pytest tests/`
5. Commit: `git commit -m "feat: add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to functions
- Keep functions focused (< 50 lines)
- Write tests for new features

## Project Structure

```
x-agent/
├── main.py           # Entry point
├── bot.py            # Telegram Bot
├── config.py         # Configuration
├── modules/          # Core modules
├── prompts/          # Prompt templates
├── niche_voices/     # Tone files
└── tests/            # Unit tests
```

## Questions?

Open an issue or reach out to the maintainers.

---

感谢您对 X-Agent 的贡献！
