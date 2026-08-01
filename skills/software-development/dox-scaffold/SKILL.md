---
name: dox-scaffold
description: "Scaffold new DOX-framework projects using Hermes Agent — generates self-referential .hermes.md root files with the full DOX protocol, plans/tasks structure, and multi-agent compatibility. Also supports adding DOX structure to existing projects via --overlay"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [scaffolding, dox, agents-md, project-template, hermes, claude-code]
    category: software-development
    related_skills: [efficient-operation, python-cli-tools]
---

# dox-scaffold — Hermes Agent Skill

Scaffold new projects using the DOX framework with **Hermes Agent** as the primary agent. Every scaffolded project gets a self-referential `.hermes.md` root file containing the full DOX protocol, a canonical `AGENTS.md` for cross-agent compatibility, and a complete `ai-docs/` hierarchy with plans and tasks.

## Prerequisites

```bash
pip install dox-scaffold
# or
uv tool install dox-scaffold
```

## Scaffold a New Project (Hermes-Aware)

```bash
dox-scaffold init <project-name> "Short description" --agent hermes
```

This generates:

```
<project-name>/
├── .hermes.md         # Hermes reads this — full DOX protocol + runtime stubs
├── AGENTS.md          # Canonical DOX contract (cross-agent compat)
├── README.md          # Customized with project name and description
├── .gitignore
├── src/               # Source code directory
└── ai-docs/
    ├── AGENTS.md      # Durable knowledge artifacts contract
    ├── plans/
    │   └── AGENTS.md  # Plan format contract with copyable template
    └── tasks/
        └── AGENTS.md  # Task lifecycle contract with copyable template
```

## Add DOX to an Existing Project

```bash
dox-scaffold init /path/to/existing-dir "Description" --agent hermes --overlay
dox-scaffold init . "Current directory" --overlay --agent hermes
```

Overlay mode:
- **Never overwrites** existing files — skips any DOX file that already exists
- Does **not** touch source code, README.md, .gitignore, or git history
- Adds only missing files: root contract + ai-docs/AGENTS.md tree
- Supports all three agent types (default, hermes, claude)
- Idempotent — re-running is a no-op

## Key Architecture: Self-Referential Root Files

Hermes loads only **one** project context file per session (priority order: `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`). The DOX protocol content must live **inline** in `.hermes.md`, not delegated to AGENTS.md, or Hermes will never see it.

| Agent | Flag | Root file generated | Subfolder hierarchy |
|-------|------|--------------------|--------------------|
| Hermes | `--agent hermes` | `.hermes.md` (self-referential DOX) + `AGENTS.md` | `AGENTS.md` (Hermes progressive discovery) |
| Default | (omitted) | `AGENTS.md` | `AGENTS.md` |
| Claude Code | `--agent claude` | `CLAUDE.md` (self-referential) + `AGENTS.md` | `AGENTS.md` + `CLAUDE.md` at every level |

The `_dox_core(agent_file)` function in the Python source generates the DOX protocol with correct file references per agent. AGENTS.md is always present as the canonical DOX contract for cross-agent compatibility.

## DOX Workflow

Projects scaffolded with `--agent hermes` follow this pipeline:

1. **Plan** — define what to build in `ai-docs/plans/P00N-name.md`
2. **Task** — decompose plans into actionable units in `ai-docs/tasks/T00N-name.md`
3. **Code** — work only against a documented task, no freeform changes
4. **Commit** — incremental, atomic commits referencing the task: `feat(scope): desc — task-NNN`

## Pitfalls

- **Shell script doesn't support `--agent`** — `./bin/dox-scaffold` is a shell wrapper that cannot generate agent-specific root files. Use `pip install dox-scaffold` and then `dox-scaffold init --agent hermes` for hermes/claude root files.
- **Project lands in CWD** — `dox-scaffold init proj "desc"` creates the project directory inside whatever directory you're currently in. If you're inside the dox-scaffold repo itself, the project gets nested there. Always run from the parent where you want the project to live.
- **Don't scaffold into an existing directory without `--overlay`** — by default, `dox-scaffold` refuses if the target exists (except when CWD causes a nested dir issue, where it silently creates). Use `--overlay` for existing projects.
- **Fill in the `.hermes.md` Run/Test/Build stubs** — they come blank, update them for your project.
- **Hermes only loads ONE root context file** — `.hermes.md` takes priority over `AGENTS.md`. The DOX protocol is IN `.hermes.md`, not delegated. This is intentional and fixed in v0.3.0+.
- **Use `--agent hermes` when scaffolding from Hermes** — the default `AGENTS.md` root works cross-agent but doesn't include Hermes runtime shortcuts.
- **Don't use paths with slashes as project names without `--overlay`** — use `--overlay` for directory paths, or just the bare name for new projects.

## Related

- Source repo: `Alignment-Foundry/dox-scaffold` at `{projects}/dox-scaffold/`
- The repo includes a distributable copy of this skill at `skills/dox-scaffold/`
- Task authoring: see `references/dox-task-authoring.md` for the DOX task file format, numbering convention, and acceptance criteria principles
