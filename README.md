# CEO Agent Workspace

A multi-agent system for autonomous project management and task coordination, orchestrated by the CEO agent (Friday).

## 🎯 What This Is

This workspace powers a 6-agent team that handles:
- **Project management** - Task allocation, progress tracking, decision coordination
- **Code development** - Frontend, backend, and integration work
- **Code review** - Quality assurance and best practices
- **Operations** - Documentation, deadlines, and workflow management

## 📦 What's Inside

### Core Configuration
- `IDENTITY.md` - Agent identity and role definition
- `SOUL.md` - Behavior guidelines and communication style
- `AGENTS.md` - Team structure and workflows
- `USER.md` - User preferences and context
- `ROUTING.md` - Responsibility boundaries
- `HEARTBEAT.md` - Periodic check-in behaviors

### Skills Directory
Pre-installed agent capabilities:
- **Development**: `git`, `github`, `api-dev`, `database-operations`, `sql-toolkit`
- **Frontend**: `react-expert`, `nextjs-expert`, `shadcn-ui`, `tailwindcss`
- **DevOps**: `docker-compose`, `docker-essentials`, `devops`
- **Tools**: `tavily-search`, `weather`, `obsidian`, `gog` (Google Workspace)
- **Utilities**: `find-skills`, `self-improving-agent`, `free-ride` (OpenRouter)

### Submodules
- `x-agent/` - External agent workspace (submodule)

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/sheldon010507-collab/x-agent.git
cd x-agent

# Agents automatically load their configuration from:
# - IDENTITY.md, SOUL.md, AGENTS.md
# - memory/ directory for session continuity
```

## 🤖 Agent Team

| Agent | Role | Reports To |
|-------|------|------------|
| **CEO (Friday)** | Project manager, coordinator | Dexter |
| **Frontend** | UI/UX, React/Next.js | CEO |
| **Backend** | API, database, logic | CEO |
| **Connection** | Integrations, config | CEO |
| **Reviewer** | Code quality, standards | CEO |
| **COO** | Operations, deadlines | CEO & Dexter |

## 📝 Memory System

- **Daily logs**: `memory/YYYY-MM-DD.md` - Raw session notes
- **Long-term**: `MEMORY.md` - Curated learnings (main session only)
- **Group chats**: Notes stored in `群聊记录/` directory

## 🔧 For Developers

This is an OpenClaw-based agent system. Key features:
- Multi-agent orchestration with clear role separation
- Telegram integration for team communication
- Obsidian-compatible note structure
- Git-based workflow with feature branches
- Self-improvement through learning logs

## 📚 Documentation

- OpenClaw docs: `/docs` or https://docs.openclaw.ai
- Skills directory: Each skill has its own `SKILL.md`
- Community: https://discord.com/invite/clawd

## 🛡️ Safety Notes

- No external data exfiltration
- Destructive commands require approval
- Private data stays local
- Uncertainty is communicated clearly

---

**Managed by Friday (CEO Agent)** 🐉  
*Making Dexter's decisions the only ones that matter.*
