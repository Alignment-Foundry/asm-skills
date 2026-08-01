# Overlap Note: project-catalog vs special-projects-manager

These two skills govern the same project system. The curator should consolidate them.

## Division of responsibility (as of current state)

| Concern | Owned by |
|---------|----------|
| **File format** (README.md + PROGRESS.md frontmatter schema, tags, append-only log) | `special-projects-manager` — this is the canonical schema |
| **When to create/update/archive** (decision rules, thresholds) | `project-catalog` — this is the lifecycle management |
| **Catalog maintenance** (CATALOG.md structure, moving entries between sections) | `project-catalog` — links to `special-projects-manager` for format |
| **Project review output format** (Telegram tables, blocker section, summary line) | `special-projects-manager` |

## Structural conflict

`project-catalog` documents project files as flat `<project-name>.md` files. The actual structure (per `special-projects-manager`) is:

```
projects/<project-name>/
├── README.md    ← No frontmatter, human-readable overview
└── PROGRESS.md  ← YAML frontmatter + append-only log
```

This was resolved during the 2026-07-25 session by patching `project-catalog` to reference the correct structure and defer to `special-projects-manager` for format conventions.
