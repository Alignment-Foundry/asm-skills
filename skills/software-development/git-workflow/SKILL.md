---
name: git-workflow
description: "Use when committing code, branching, rebasing, or managing PRs. Provides commit message conventions, branching strategy, and git workflow rules."
version: 1.0.0
author: ASM Skills
license: MIT
metadata:
  hermes:
    tags: [git, commits, branching, workflow]
    related_skills: [code-review]
---

# Git Workflow — Commit Conventions & Branching

Use this skill when writing commits, creating branches, opening PRs, or managing git history.

## Commit Message Convention

```
<type>(<scope>): <short description>

<body (optional)>

<footer (optional)>
```

### Types

| Type | When to Use |
|------|------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, whitespace (no code change) |
| `refactor` | Code restructuring (no behavior change) |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `chore` | Build, CI, dependencies |
| `revert` | Reverting a previous commit |

### Rules

1. **Short description**: ≤ 72 chars, imperative mood ("Add" not "Added" or "Adds")
2. **Body**: Wrap at 72 chars, explain *why* not *what*
3. **Scope**: Optional but preferred — module, component, or area (e.g., `feat(auth):`)
4. **No period** at end of the subject line

### Examples

```
feat(auth): add OAuth2 refresh token rotation

Rotates refresh tokens on each use to prevent replay attacks.
Migrates existing sessions to new token format.
```

```
fix(api): handle null response from payment gateway

Check for null in the callback before accessing response fields.
Prevents 500 errors when the gateway returns an unexpected format.
```

## Branching Strategy

### Branch Naming

```
<type>/<short-description>
```

Examples: `feat/oauth-refresh`, `fix/payment-null`, `docs/api-readme`

### Flow

1. Branch from `main`
2. Commit with conventional messages
3. Open PR → `main`
4. Squash-merge (keeps linear history)

### Before Opening a PR

- [ ] Rebase on latest `main`: `git rebase main`
- [ ] No merge commits in branch history
- [ ] All commits follow convention
- [ ] Branch name matches the change type

## Common Pitfalls

1. **Don't use `git pull --rebase`** on shared branches — only rebase your feature branch
2. **Don't amend pushed commits** — always add a new commit or squash at merge time
3. **Write commit messages for your future self** — six months from now, the diff shows *what*, the message shows *why*
