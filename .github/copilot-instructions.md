## About this repo

This is **asm-skills** — a portable repository of agent skills compatible with Hermes Agent, Claude Code, and GitHub Copilot.

The canonical project specification is [SKILL.md](../SKILL.md) (agentskills.io format).

- Skills live in `skills/<category>/<name>/` — each is a single `SKILL.md` with markdown instructions (YAML frontmatter + body)
- `SKILL.md` is the canonical format at both root and per-skill level
- `AGENTS.md`, `CLAUDE.md`, and `.github/copilot-instructions.md` all reference `SKILL.md` as canonical

When helping with code, check these categories:
- `skills/productivity/` — project tracking, reviews, diagnostics
- `skills/software-development/` — git workflow, CLI tools, MCP servers, test fixtures
- `skills/security/` — credential management
- `skills/autonomous-ai-agents/` — agent orchestration
- `skills/github/` — repo management
- `skills/mlops/` — ML observability
- `skills/monitoring/` — credit/balance monitoring
