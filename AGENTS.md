# ASM Skills — Agent Instructions

## Canonical Source

The canonical project specification is [SKILL.md](SKILL.md) (agentskills.io format). Read it first for the full skill listing, quick start, and creation guide.

## How to Use This Repo

1. Read [SKILL.md](SKILL.md) — canonical project spec with full skill index
2. Each skill in `skills/<category>/<name>/` is a single `SKILL.md` — YAML frontmatter + markdown, readable by every agent
3. **Scripts in `scripts/`** validate and install skills

## Available Skills by Category

### autonomous-ai-agents/
- `paperclip-company` — Model a business as a Paperclip company

### github/
- `github-org-ops` — Cross-org GitHub operations, repo migration, PAT management

### mlops/
- `langfuse` — LLM observability, prompt management, evals

### monitoring/
- `nous-credits-check` — Nous Portal credits balance checking

### productivity/
- `code-review` — Pre-commit code review checklist & workflow
- `digital-chief-of-staff` — AI Chief of Staff infrastructure setup
- `local-tts` — Local offline neural text-to-speech
- `network-connectivity-diagnostics` — Systematic network diagnostics
- `project-catalog` — Project catalog management
- `special-projects-manager` — YAML-frontmatter project tracking
- `structured-reference-delivery` — Multi-source research to formatted files

### security/
- `password-store-vault` — GPG-encrypted credential vault with pass

### software-development/
- `cross-agent-skill-repo` — Building portable skill repos
- `dox-scaffold` — DOX-framework project scaffolding
- `efficient-operation` — Token-efficient deterministic operations
- `git-workflow` — Commit conventions & branching
- `markdown-publishing` — Structured markdown publishing
- `mcp-server-builder` — MCP server creation from scratch
- `python-cli-tools` — Modular Python CLI tool building
- `test-fixture-authoring` — Synthetic test data generation

## For Agents Without Native Skill Loading

Read `skills/<category>/<name>/SKILL.md` directly with `read_file` and follow the instructions within.
