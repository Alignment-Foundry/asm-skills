---
name: cross-agent-skill-repo
description: "Use when building a portable skill repository that works across Hermes Agent, Claude Code, and GitHub Copilot from a single source of truth."
version: 2.0.0
author: ASM Skills
license: MIT
metadata:
  hermes:
    tags: [skills, repository, cross-agent, hermnes-agent, claude-code, copilot, portability]
    related_skills: [hermes-agent-skill-authoring, github-repo-management, special-projects-manager]
---

# Cross-Agent Skill Repository

Build a portable, agent-agnostic skill repository that works with **Hermes Agent**, **Claude Code**, **GitHub Copilot**, and any agent that reads markdown — from a single source of truth.

## When to Use

- User asks you to create a repo of reusable agent skills
- User references `asm-skills` or a skills repo that should work across multiple agents
- You're tasked with building a skill library that's not tied to a single agent runtime
- Porting Hermes-local skills into a shareable, version-controlled repo

## Architecture

### Single Format Per Skill

Each skill in `<category>/<name>/` ships one file:

| File | Format | Consumed By |
|------|--------|-------------|
| `SKILL.md` | YAML frontmatter + markdown | **All agents** — Hermes Agent (native, loaded via `skill_view` or installed to `~/.hermes/skills/`), Claude Code, GitHub Copilot, Cursor, Windsurf, and any agent that reads markdown |

### Root Config Files

| File | Consumer | Purpose |
|------|----------|---------|
| `AGENTS.md` | Generic agents (Claude Code, Cursor, Windsurf, etc.) | Tells agents about the `skills/` directory structure and how to read skills |
| `CLAUDE.md` | Claude Code specifically | Claude Code-specific instructions pointing to `skills/` tree |
| `.github/copilot-instructions.md` | GitHub Copilot | Copilot context pointing to `skills/` tree |
| `README.md` | Everyone | Project entry point, directory overview, quick start commands |

**Key rule**: Root configs point TO the shared `skills/` tree — they do NOT duplicate skill content. The tree is the single source of truth.

### Directory Structure

```
<repo-name>/
├── README.md                    # Project overview
├── AGENTS.md                    # Generic agent instructions
├── CLAUDE.md                    # Claude Code instructions
├── .github/
│   └── copilot-instructions.md  # Copilot instructions
├── skills/                      # All skills, single source of truth
│   ├── _template/               # Template for contributors
│   │   └── SKILL.md             # Single skill file (YAML frontmatter + body)
│   ├── <category>/              # e.g. productivity/, software-development/
│   │   └── <skill-name>/
│   │       └── SKILL.md         # Single skill file (YAML frontmatter + body)
│   └── ...
├── scripts/
│   ├── validate-skills.py       # Validates all SKILL.md frontmatter
│   └── sync-skill.sh            # Installs a skill to Hermes local dir
└── LICENSE
```

## Workflow: Porting Existing Hermes Skills

Use this when the task involves taking skills already installed under `~/.hermes/skills/` (or the active profile's `skills/`) and publishing them in a shareable repo.

### 1. Identify User-Created vs Bundled Skills

Hermes ships with a set of bundled skills. User-created skills are the extras. To identify them:

```bash
# Get the list of bundled skill names
cat ~/.hermes/profiles/<profile>/skills/.bundled_manifest | cut -d'|' -f2 | cut -d':' -f1 | sort

# Get all installed skill names
find ~/.hermes/profiles/<profile>/skills -maxdepth 3 -name SKILL.md | while read -r f; do
    basename "$(dirname "$f")"
done | sort

# User-created = installed minus bundled
```

Bundled skills are protected — skip them. Only port user-created skills.

### 2. Read Each User-Created Skill

Before porting, read each skill's `SKILL.md` to understand its structure and verify it's complete. Key info to extract:
- `name` and `description` from frontmatter
- Supporting directories: `references/`, `scripts/`, `templates/`, `assets/`
- Linked files from `skill_view()` output

### 3. Port Each Skill

For each user-created skill, one file is needed:

**`SKILL.md`** — Copy as-is (Hermes format with YAML frontmatter):
```bash
cp ~/.hermes/profiles/<profile>/skills/<category>/<name>/SKILL.md \
   repo/skills/<category>/<name>/SKILL.md
```

**Generalize industry-specific language** (before copying): If the skill was built with examples from one vertical (insurance, healthcare, SaaS), strip that language to make it portable. Replace carrier names, specific subreddits, trade publications, and industry jargon with generic equivalents. See the `paperclip-company` skill's `references/skill-generalization-workflow.md` for a detailed find-replace pattern and scan-target checklist.

### 4. Copy Supporting Files

Each skill may have supporting directories. Copy them recursively, **excluding** Hermes-internal files:

```python
SKIP_FILES = {".curator_backups", ".curator_state", ".hub",
              ".usage.json", ".usage.json.lock"}

for src_path in source_dir.rglob("*"):
    # Skip Hermes-internal files at any depth
    if any(p.name in SKIP_FILES for p in src_path.relative_to(source_dir).parents):
        continue
    if src_path.name in SKIP_FILES:
        continue
    # Copy to target
```

Supporting directories by purpose:
| Directory | Content Type | Example |
|-----------|-------------|---------|
| `references/` | Session detail, API docs, error transcripts | `references/pat-limitations.md` |
| `scripts/` | Runnable automation | `scripts/validate-skills.py` |
| `templates/` | Boilerplate to copy/modify | `templates/PROGRESS.md` |
| `assets/` | Images, binaries, data files | `assets/logo.png` |

### 5. Create a Port Script (Recommended)

For 5+ skills, write a port script (see `scripts/port-skills.py` pattern):

```python
#!/usr/bin/env python3
"""Port user-created Hermes skills to asm-skills repo.

For each skill:
  SKILL.md → copied as-is
  All supporting files copied (references/, scripts/, templates/)
"""

import shutil
from pathlib import Path

USER_SKILLS_DIR = Path.home() / ".hermes" / "profiles" / "<profile>" / "skills"
REPO_SKILLS_DIR = Path("skills")

def port_skill(source_dir, target_dir):
    target_dir.mkdir(parents=True, exist_ok=True)
    # Copy all files (skip Hermes internals)
    for src in source_dir.rglob("*"):
        if any(p.name in SKIP_FILES for p in src.relative_to(source_dir).parents):
            continue
        # ... copy logic
```

Run the port script, then validate:
```bash
python3 scripts/port-skills.py
python3 scripts/validate-skills.py
```

### 6. Set Up GitHub Repo and Push

After all skills are ported:

```bash
# Create the repo
curl -X POST -H "Authorization: Bearer $GH_TOKEN" \
  https://api.github.com/orgs/Alignment-Foundry/repos \
  -d '{"name":"asm-skills","private":false,"auto_init":false}'

# Init and push
cd repo
git init
git branch -m main
git remote add origin https://github.com/Alignment-Foundry/asm-skills.git
git add -A
git commit -m "Initial commit"
git push -u origin main
```

**PAT note**: A fine-grained PAT (`github_pat_...`) must be authorized for the target org. If `gh repo create` fails with "does not have the correct permissions," use the token directly via curl (the `.git-credentials` file may hold a token under a different GitHub account than the `gh` CLI is logged into — check both `~/.git-credentials` and the profile's fake home `.git-credentials`).

## Workflow: Creating the Repo (from scratch)

### 1. Initialize the Project

```bash
mkdir -p <repo-name>/skills/{productivity,software-development}
cd <repo-name>
git init
```

### 2. Create Root Configs

Write each config file to tell its agent about the `skills/` tree. Keep them brief — they're pointers, not content.

**`AGENTS.md`** — Generic:
```
# <Repo Name> — Agent Instructions

This repository contains portable agent skills in `skills/<category>/<name>/`.

## How to Use

1. Read the skill's `SKILL.md` — one file works for every agent.
2. Scripts in `scripts/` validate and install skills.
```

**`CLAUDE.md`** — Claude Code-specific:
```
# <Repo Name> — Claude Code Instructions

Each skill in `skills/<category>/<name>/` is a single `SKILL.md` in markdown.

To use a skill: read `skills/<category>/<name>/SKILL.md` and follow its instructions.
```

**`.github/copilot-instructions.md`** — Copilot:
```
## About this repo

<Repo Name> — portable agent skills compatible with Hermes, Claude Code, and Copilot.

Skills live in `skills/<category>/<name>/` — each is a single `SKILL.md` with instructions.
```

### 3. Create the Template Skill

Create `skills/_template/` with a single `SKILL.md` (full YAML frontmatter + markdown body).

**`SKILL.md` frontmatter template:**
```yaml
---
name: _template
description: "Template for creating new skills. Copy this directory to create a new skill."
version: 1.2.0
author: ASM Skills
license: MIT
metadata:
  hermes:
    tags: [template, meta]
    related_skills: []
---
### 4. Create Sample Skills

Seed the repo with 1-2 useful skills that demonstrate the single-file pattern. Good candidates:
- `productivity/code-review/` — pre-commit quality gates and review checklist
- `software-development/git-workflow/` — commit message conventions and branching

Each sample skill is a single `SKILL.md`.

### 5. Write Validation Script

```python
#!/usr/bin/env python3
"""Validate all SKILL.md files in skills/.

Checks:
- Starts with --- (byte 0)
- YAML frontmatter parses correctly
- name and description fields present
- Description <= 1024 chars
- Body is non-empty
- Total file size <= 100KB
"""
```

Store at `scripts/validate-skills.py`. Make executable (`chmod +x`).

### 6. Write Sync Script

```bash
#!/usr/bin/env bash
# sync-skill.sh — Install a skill to Hermes local skills directory.
# Usage: bash scripts/sync-skill.sh <category>/<skill-name> [--copy]
#
# --copy copies instead of symlinking (for independent editing).
```

Store at `scripts/sync-skill.sh`. Make executable.

### 7. Validate and Push

```bash
python3 scripts/validate-skills.py     # All skills must pass
git add .
git commit -m "Initial commit: repo structure + template + sample skills"
```

### 8. Sanitize Credentials Before Publishing (CRITICAL)

Before pushing to a **public** repo, scan every skill for leaked credentials and PII. User-created skills often contain API keys, tokens, passwords, or phone numbers from session examples and reference docs.

Add audit scripts to the repo and run them pre-push:

**`scripts/audit-credentials.py`** — Scans all files for 20+ API key/token patterns:
```python
PATTERNS = {
    "GitHub fine-grained PAT": r"github_pat_[a-zA-Z0-9]{50,}",
    "GitHub classic PAT": r"ghp_[a-zA-Z0-9]{36,}",
    "OpenAI API key": r"sk-[a-zA-Z0-9]{20,}",
    "AWS access key": r"AKIA[0-9A-Z]{16}",
    "Telegram bot token": r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}",
    "Stripe secret key": r"sk_live_[a-zA-Z0-9]{10,}",
    "URL-embedded credentials": r"https?://[^:]+:[^@]{10,}@",
    "PEM private key": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    "JWT-like token": r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    # ... plus all standard providers
}
```

**`scripts/audit-pii.py`** — Scans for emails, phone numbers, and IPs not in known-safe ranges:
- Skips `user@gmail.com`, `git@github.com`, `127.0.0.1`, `192.168.x.x`, `0.0.0.0`, `224.0.0.x` automatically
- Flags unredacted phone numbers and real-looking emails

**Pre-push workflow:**
```bash
python3 scripts/audit-credentials.py  # Should return 0
python3 scripts/audit-pii.py          # Should return 0
git add -A
git commit -m "message"
# Then push with appropriate PAT
```

### Git History Cleanup

If credentials were committed (even briefly), **file-level sanitization is not enough** — the old data survives in git history. Anyone can `git log -p` to recover it.

Use `git-filter-repo` to rewrite history:

```bash
pip install git-filter-repo
git filter-repo --replace-text /tmp/replacements.txt --force
```

See `references/git-history-cleanup-filter-repo.md` for the full workflow: identifying sensitive strings, creating replacement files, callbacks for author metadata, path obfuscation rules, and force-push.

Without this step, sanitizing the current files is theatre — the history still leaks everything.

**Common sanitization fixes discovered in real use:**
- PAT prefixes in reference docs (`github_pat_11AWOV...`) — redact to generic `<PAT>` 
- Real phone numbers in CLI tool example output — change to `(555) 123-4567`
- Personal file paths (`/home/user/.hermes/profiles/profilename/`) — obfuscate with `{placeholder}` patterns
- AWS example keys — replace with explicit `<AKIA_EXAMPLE_KEY>` placeholder
- File paths to credential stores (`/home/<user>/.hermes/profiles/<profile>/home/.git-credentials`) — redact to generic description
- Account names (`{account}-dev`) in public docs — redact if identifying

After sanitizing, re-run both audits to confirm zero findings, then commit and push.

## Publishing Gate (public repos)

The repo is a **curated, genericized publication subset** — not a mirror of local stores. Local skills stay specific to the owner's use; published copies are generic derivatives. Before anything new is published:

1. **Holdlist check** — `.publish-holdlist.md` (gitignored, private) tracks review state: `pending-review` (default for any new/updated skill) → `approved` (publishable) / `blocked` (never publish). `port-skills.py` skips anything not `approved`.
2. **Genericness audit** — `scripts/audit-generic.py` reads the PRIVATE `.audit-generic-markers.json` (gitignored; schema: proper_nouns / projects / orgs / jargon / paths marker categories). Any hit = not publish-ready.
3. **Agent genericization** — genericize the repo copy per the `paperclip-company` skill's `references/skill-generalization-workflow.md` rubric; the local copy stays untouched.
4. **Security audits** — `audit-credentials.py` + `audit-pii.py` must exit 0 (public repo).
5. **Owner checkpoint** — pending-review items surface in the daily digest for approval; only approved skills get pushed.

Private files are gitignored **by design** — CI runs generic checks against the committed example markers (`.audit-generic-markers.example.json`, placeholders only); the real enforcement is the local pre-push gate.

## Creating a New Skill (for Contributors)

1. **Copy the template**: `cp -r skills/_template skills/<category>/<skill-name>/`
2. **Edit SKILL.md**:
   - Update `name` (lowercase, hyphens, ≤64 chars)
   - Write `description` starting with "Use when ..." (≤1024 chars)
   - Set version, author, tags
   - Replace body with the skill's content
3. **Validate**: `python3 scripts/validate-skills.py`
4. **Install locally**: `bash scripts/sync-skill.sh <category>/<skill-name>`

## Hermes SKILL.md Format Rules

(From `hermes-agent-skill-authoring` — key constraints for the SKILL.md file:)

- Starts with `---` at byte 0 (no leading blank line)
- Closes with `\n---\n` before the body
- YAML frontmatter parses as a mapping
- `name` field: lowercase + hyphens, ≤64 chars
- `description` field: ≤1024 chars
- Body after frontmatter: non-empty
- Total file: ≤100,000 chars (aim for 8-15KB)

## Common Pitfalls

1. **Don't create per-skill README.md files** — the global standard is ONE `SKILL.md` per skill. A second README.md duplicates content, drifts out of sync, and breaks the single-source-of-truth rule. The validator neither requires nor generates README.md.
2. **Duplicate skill content across root configs** — AGENTS.md, CLAUDE.md, and copilot-instructions.md should POINT to `skills/`, not repeat skill bodies. The tree is the single source of truth.
3. **Hermes-specific tool references in SKILL.md** — keep the body agent-neutral: prefer "read this file" over "load with skill_view()" so every agent can follow it.
4. **Forgetting the LICENSE** — without a license, a public skill repository can't be used by others. Prefer MIT for permissive reuse.
5. **Overwriting user-local Hermes skills** — `sync-skill.sh` uses `rm -rf "$TARGET"` before linking. Warn the user if they have local modifications.

## Verification Checklist

- [ ] Root configs exist: `README.md`, `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`
- [ ] `skills/_template/` has a single `SKILL.md` (no README.md)
- [ ] Every skill in `skills/<category>/<name>/` has a single `SKILL.md` (no README.md)
- [ ] `scripts/validate-skills.py` exists, executable, returns zero for all skills
- [ ] `scripts/sync-skill.sh` exists, executable
- [ ] `LICENSE` file present (MIT recommended for public repos)
- [ ] `.gitignore` present (at minimum `__pycache__/`, `*.pyc`)
- [ ] All `SKILL.md` files pass `python3 scripts/validate-skills.py`
- [ ] No `SKILL.md` has a `name` field that collides with another skill (name uniqueness in Hermes is global)
