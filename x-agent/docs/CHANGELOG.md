# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-03-26

### Added
- **Multi-Platform Research**: Deep integration with last30days-skill for 8+ platform data collection
- **Niche Switching**: One-command niche switching via `/set_niche` Telegram command
- **Anti-Ban System**: Random delays, content variants, and daily limits for safe automation
- **4-Dimensional Scoring**: Relevance, Velocity, Authority, Convergence scoring system
- **7 Pre-built Niches**: adult_uk, ai_tools, beauty, fitness, crypto, humor, custom
- **Multi-LLM Support**: OpenAI, Anthropic, Gemini, DeepSeek, Moonshot, Qwen, Zhipu
- **Structured Prompts**: Type A (tweets), Type B (video scripts), Type C (comments)
- **Logging System**: Console + file logging with timestamps
- **Docker Support**: docker-compose.yml for easy deployment

### Changed
- Repository structure reorganized (single x-agent/ directory)
- Old versions archived in archive/ folder
- Research module rewritten for real API integration
- Scorer upgraded to use last30days fields

### Fixed
- Mock data replaced with real API calls
- Missing prompt templates created
- Missing database schema added

## [2.0.0] - 2026-03-20

### Added
- Supabase database integration
- OpenClaw bridge for safe automation
- Multi-LLM router with fallback
- Content generator (A/B/C types)
- Daily review system
- Unit tests

### Changed
- Modular architecture
- Async/await patterns
- Configuration via .env

## [1.0.0] - 2026-03-15

### Added
- Initial release
- Basic X research functionality
- Single LLM support (OpenAI)
- Simple scoring system
- Telegram bot basics
