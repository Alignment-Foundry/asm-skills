---
name: code-review
description: "Use when performing pre-commit code review, security scanning, or quality gates before merging. Provides a structured checklist and automated review process."
version: 1.0.0
author: ASM Skills
license: MIT
metadata:
  hermes:
    tags: [code-review, quality, security, pre-commit]
    related_skills: [git-workflow, requesting-code-review]
---

# Code Review — Pre-Commit Quality Gates

Use this skill when the user asks you to review code, check for issues before commit, or run quality gates on a PR or branch.

## Workflow

### 1. Security Scan

Check for common vulnerabilities before reading any code deeply:

- **Hardcoded secrets**: API keys, tokens, passwords, private keys in source
- **Injection vectors**: Raw SQL concatenation, shell command building with user input, `eval()` usage
- **Path traversal**: Unsanitized file paths from user input
- **Dependency issues**: Known-vulnerable versions (check `requirements.txt`, `package.json`, etc.)

### 2. Quality Gates

| Gate | What to Check |
|------|--------------|
| Lint | Unused imports, undefined variables, syntax errors |
| Type safety | Missing type annotations on function signatures, `Any` overuse |
| Error handling | Bare `except:`, swallowed exceptions, missing `finally` |
| Logging | `print()` in production code, missing structured logging |
| Testing | New functions without tests, removed tests, hardcoded test data |

### 3. Structural Review

- **Single Responsibility**: Does each function/module do one thing?
- **Duplication**: Repeated logic that should be extracted
- **Naming**: Clear, intention-revealing names (not `x`, `data`, `temp`)
- **Complexity**: Functions over 50 lines or with 4+ nesting levels need refactoring

### 4. Reporting

Report findings grouped by severity:

```
🔴 **CRITICAL** — Must fix before merge
- ...
🟡 **WARNING** — Should address
- ...
🔵 **SUGGESTION** — Nice-to-have
- ...
```

## Common Pitfalls

1. **Don't review formatting** — let the linter/formatter handle that
2. **Don't suggest architecture rewrites** in a PR review — open an issue instead
3. **Always verify** security findings — false positives waste time
4. **Read the diff, not the whole file** — focus on changed lines unless a security finding requires broader context
