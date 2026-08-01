# DOX Task File Authoring Guide

How to write task files for DOX-framework projects. Task files live at `ai-docs/tasks/T00N-<slug>.md` in the project repo.

## When to Write DOX Task Files

Write DOX task files when:
- A plan has been approved and the user says "flush into tasks"
- Decomposing a feature into implementation units
- Delegating work to subagents

## Task File Format

```markdown
---
title: "Short Feature Title"
feature: "feature-slug"
status: pending
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
---

# T00N: Short Feature Title

## Goal

One-sentence goal describing what this task builds.

## Acceptance Criteria

- [ ] Bullet list of checkable criteria
- [ ] Each criterion is verifiable (test, CLI output, visual check, etc.)

## Files to Modify

- `path/to/file.py` — what changes and why
- `path/to/new_file.py` — new file, what it provides

## Commit Message

```
feat(scope): description — task-NNN
```

## Notes

Optional: edge cases, trade-offs, open questions, or implementation sketches.
```

## Numbering Convention

- Sequential: T001, T002, T003...
- Check existing task files in `ai-docs/tasks/` before numbering
- If the highest existing is T013, start the next batch at T014

## Commit Message Convention

| Type | Scope | Example |
|------|-------|---------|
| `feat` | module/area | `feat(wiki): add --obsidian flag` |
| `fix` | module/area | `fix(cli): handle empty pages on build` |
| `refactor` | module/area | `refactor(models): extract frontmatter builder` |
| `chore` | module/area | `chore(repo): transfer to alignment-foundry` |

Always append `— task-NNN` to the commit message.

## Lifecycle States

| Status | Meaning |
|--------|---------|
| `pending` | Created but not started |
| `in_progress` | Actively being worked on |
| `completed` | Acceptance criteria met, committed |
| `cancelled` | Abandoned or superseded |

## Acceptance Criteria Principles

- **Verifiable** — each item must be checkable without guessing
- **Atomic** — one criterion per behavior
- **Test-driven** — prefer "tests pass" over "code compiles"
- **Edge-case aware** — include error states, empty states, boundary conditions

## Files-to-Modify Principles

- Be explicit: `src/module/file.py` not just "the config file"
- Note whether it's being created or modified
- Add a one-liner on what changes (the "why")
- Include test files alongside source files

## Implementation Sketch (Notes Section)

For complex tasks, include a Notes section with:
- Architecture approach
- Key design decisions
- LLM prompts (if the task involves LLM integration)
- Data flow diagram (text-based)

The sketch should be enough that a subagent with zero project context can build the task correctly.
