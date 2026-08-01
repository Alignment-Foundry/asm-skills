---
name: asm-skills
description: "A portable, agent-agnostic repository of reusable skills for AI coding agents. Use when building skill libraries that work across Hermes Agent, Claude Code, and GitHub Copilot from a single source of truth."
license: MIT
metadata:
  author: Alignment-Foundry
  version: "1.0.0"
  tags:
    - skills
    - hermes-agent
    - claude-code
    - copilot
    - agent-tooling
    - cross-platform
---

# ASM Skills

A portable, agent-agnostic repository of reusable skills for AI coding agents. Designed to work with **Hermes Agent**, **Claude Code**, and **GitHub Copilot** from a single source of truth.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/alignment-foundry/asm-skills.git
cd asm-skills

# Validate all skills
python3 scripts/validate-skills.py

# Install a skill for Hermes (symlinks to ~/.hermes/skills/)
bash scripts/sync-skill.sh productivity/code-review

# Create a new skill from the template
cp -r skills/_template skills/<category>/<your-skill-name>
```

## How It Works

Each skill lives in `skills/<category>/<name>/` as a single file:

| File | Format | Used By |
|------|--------|---------|
| `SKILL.md` | YAML frontmatter + markdown | **All agents** — Hermes Agent (native), Claude Code, Copilot, Cursor, and any agent that reads markdown |

All root-level agent files (`CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`) reference this `SKILL.md` as the canonical project source.

## Agent Compatibility

| Agent | Entry Point | How to Load a Skill |
|-------|-------------|-------------------|
| **Hermes Agent** | `AGENTS.md` → `SKILL.md` | `skill_view(name='code-review')` or `skills_list()` |
| **Claude Code** | `CLAUDE.md` → `SKILL.md` | `read_file(skills/productivity/code-review/SKILL.md)` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Reads skill `SKILL.md` from context |

## Available Skills

### Autonomous AI Agents
- `paperclip-company` — Model a real business as a Paperclip company

### GitHub
- `github-org-ops` — Cross-organization GitHub operations, repo migration, PAT management

### MLOps
- `langfuse` — LLM observability, prompt management, and evals

### Monitoring
- `nous-credits-check` — Check and report Nous Portal credits balance

### Productivity
- `code-review` — Pre-commit review checklist — security scan, quality gates, structural review
- `digital-chief-of-staff` — Bootstrapping infrastructure for an AI agent acting as a digital Chief of Staff
- `local-tts` — Install and configure local/offline neural text-to-speech
- `network-connectivity-diagnostics` — Systematic network diagnostics from service layer down to WiFi
- `project-catalog` — Manage project catalog with create, update, archive workflows
- `special-projects-manager` — YAML-frontmatter project tracking with PROGRESS.md and progressive disclosure
- `structured-reference-delivery` — Multi-source research → formatted Excel/CSV deliverables

### Security
- `password-store-vault` — GPG-encrypted credential vault with pass, browserpass, and Tailscale sync

### Software Development
- `cross-agent-skill-repo` — Build portable skill repos working across Hermes, Claude Code, and Copilot
- `dox-scaffold` — Scaffold DOX-framework projects with plans, tasks, and multi-agent setup
- `efficient-operation` — Token-efficient, concise, deterministic-first operations
- `git-workflow` — Commit message conventions, branching strategy, and git workflow rules
- `markdown-publishing` — Convert structured markdown with Mermaid, MARP, and references
- `mcp-server-builder` — Build new MCP servers from scratch with architecture, DB, testing
- `python-cli-tools` — Modular Python CLI tools with async sources and Docker packaging
- `test-fixture-authoring` — Realistic synthetic test data for SIT/UAT with hidden acceptance criteria

## Creating a New Skill

See the [`_template`](./skills/_template/) directory for a starting point. Each skill needs:

1. `SKILL.md` — YAML frontmatter with `name`, `description`, `version`, `author`, `license`, and `metadata.hermes.tags`
   followed by the markdown body — one file readable by every agent

## Validation

```bash
python3 scripts/validate-skills.py
```

Checks every `SKILL.md` for:
- Valid YAML frontmatter (starts with `---`, parses correctly)
- `name` and `description` fields present
- Description ≤ 1024 chars
- Non-empty body after frontmatter
- File size ≤ 100 KB
