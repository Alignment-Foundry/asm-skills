---
name: _template
description: "Template for creating new skills in the asm-skills repository. Copy this directory to create a new skill."
version: 1.0.0
author: ASM Skills
license: MIT
metadata:
  hermes:
    tags: [template, meta]
    related_skills: []
---

# _template — Skill Template

> ⚠️ This is a template directory. Copy it to create a new skill, then edit the files.

## Structure

- `SKILL.md` — the single skill file (YAML frontmatter + markdown body), readable by all agents

## Instructions for Creating a Skill

1. **Copy** this entire directory: `cp -r skills/_template skills/<category>/<your-skill-name>/`
2. **Edit** `SKILL.md`:
   - Update the `name` field (lowercase, hyphens, ≤64 chars)
   - Write a `description` that starts with "Use when ..." (≤1024 chars)
   - Set your version, author, tags
   - Replace the body with your skill's actual content
3. **Validate**: `python3 scripts/validate-skills.py`
4. **Install** locally: `bash scripts/sync-skill.sh <category>/<skill-name>`

## Formatting Rules

- All files are UTF-8 markdown
- `SKILL.md` must start with `---` at byte 0
- Description must be ≤ 1024 characters
- Body must be non-empty after the frontmatter
- Use targets like "You" for the agent and "user" for the human
