# ASM Skills — Claude Code Instructions

## Canonical Source

Read [SKILL.md](SKILL.md) first — it is the canonical project specification (agentskills.io format) with the full skill listing, quick start, and creation guide.

## For Claude Code

Each skill in `skills/<category>/<name>/` is a single `SKILL.md` with the skill's instructions in markdown. To use a skill:

```
Read skills/<category>/<name>/SKILL.md for full skill context, then follow its instructions.
```

## Available Skills

| Category | Skills |
|----------|--------|
| `autonomous-ai-agents/` | paperclip-company |
| `github/` | github-org-ops |
| `mlops/` | langfuse |
| `monitoring/` | nous-credits-check |
| `productivity/` | code-review, digital-chief-of-staff, local-tts, network-connectivity-diagnostics, project-catalog, special-projects-manager, structured-reference-delivery |
| `security/` | password-store-vault |
| `software-development/` | cross-agent-skill-repo, dox-scaffold, efficient-operation, git-workflow, markdown-publishing, mcp-server-builder, python-cli-tools, test-fixture-authoring |

Read any skill's `SKILL.md` directly:
```
read_file(skills/productivity/code-review/SKILL.md)
```

## Format

Every skill is a single `SKILL.md` (YAML frontmatter + markdown) — the same file works for Hermes Agent, Claude Code, and Copilot.
