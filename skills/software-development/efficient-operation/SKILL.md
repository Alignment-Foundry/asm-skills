---
name: efficient-operation
description: "Token-efficient, concise, deterministic-first operations."
version: 1.4.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [efficiency, token-awareness, conciseness, determinism, scripting, platform-ops]
    category: software-development
    related_skills: [claude-code, simplify-code]
---

# Efficient Operation Skill

General operating principles — be concise, token-efficient, and default to deterministic over LLM reasoning.

## Core Philosophy

Every token has a cost; every LLM turn burns cache. Default to the cheapest solution that correctly solves the problem.

## Platform Interaction (CLI-First)

For cloud/SaaS platform management (fly.io, GCP, AWS, Vercel, etc.):
- Default to CLI tools (flyctl, gcloud, aws-cli, gh, etc.) for all operations — never the web UI.
- Browser automation on management dashboards triggers bot detection and is unreliable for routine tasks.
- The browser is reserved exclusively for live interactive sessions where the user is watching and co-piloting.
- If no CLI exists for a platform task, flag it to the user rather than trying to automate the web UI.

## The Token Ladder

Climb from the cheapest rung up. Only go higher when the task genuinely needs reasoning.

1. **Hermes core tools** (patch, read_file, search_files, terminal) — lowest cost. Use for mechanical edits, file ops, grep/awk, git commands.
2. **execute_code** — lightweight Python scripts with tool access. Use for 3+ tool calls with processing, filtering, or loops between them.
3. **Deterministic script** (write a .sh/.py then run it) — batch ops, repetitive patterns, CI commands. Scripts cost nothing to re-run.
4. **Print-mode Claude (`-p`) with haiku** — cheap reasoning: linting, simple refactors, summaries.
5. **Print-mode Claude (`-p`) with sonnet/opus** — hard problems: complex refactors, multi-file coordination, deep code review.
6. **Interactive tmux Claude** — last resort. Only for multi-turn sessions where print mode cannot work.

## Scripts Over LLM Reasoning

- Mechanical ops (rename, format, lint, batch search-replace) → patch, sed, ruff --fix, prettier, black, git — never pay LLM tokens for this.
- If a well-known tool or package exists for the job, use it instead of having Claude reinvent it.
- For repetitive multi-step tasks, write a script once and invoke it; don't re-derive the approach each time.

## Task-First Development Workflow

When building multi-step features across several tasks:

1. **Write all task files first** — before any code, create `ai-docs/tasks/TNNN-*.md` task files for every task in the phase. Each task has: a one-sentence Goal, checkbox Acceptance Criteria, Implementation Notes with file paths, and a commit message template.
2. **One task = one atomic commit** — commit after each task, not after the whole phase. Each commit message references the task: `feat(scope): description — task-NNN`.
3. **Deliver incremental, not bulk** — the user reviews per-task output and can course-correct between commits.
4. **End phases with a structured summary** — a table of deliverables, test counts, and what was built. Example:
   ```
   ## Phase N Complete ✅
   **X tests passing, 0 failures.** Here's what was built:
   | # | Task | What | Commit |
   |---|------|------|--------|
   | T001 | Setup | ... | `abc1234` |
   | T002 | Core | ... | `def5678` |
   ```

This workflow pairs with the DOX framework — task files live under `ai-docs/tasks/`, plans under `ai-docs/plans/`.

## Prompting Guidelines

- Prompts are **commands, not paragraphs**. State exactly what to do — no context re-explaining what's already in the conversation, no backstory, no fluff.
- When delegating to Claude Code, always set `--max-turns` (3-5 simple, 10-15 complex) and `--allowedTools` (Read,Edit,Bash for most).
- Pipe known data (git diff, file contents) instead of having Claude discover it — saves discovery turns.
- Never use an LLM to do what a one-line shell command can do.

## External Reference Integration

When given an external reference (gist, paper, article, API doc) and asked to integrate its insights into a project, use this pattern:

### Workflow

1. **Fetch and capture the raw source** — save it as an immutable reference doc (e.g. `ai-docs/sources/<source-name>.md`). This is the "raw layer" — never edited, only read.

2. **Read the target project** — understand the codebase, its current architecture, the core insight it embodies. This means reading README, AGENTS.md, source files, pyproject.toml, template files. Don't skip this step — you need the full picture before you can map.

3. **Map concepts from reference to project** — for each major idea in the reference, ask: "Does the project already do this? Partially? Not at all?" Build a comparison table.

4. **Identify gaps and improvement opportunities** — what does the reference enable that the project doesn't yet support? What would the project look like if it fully embodied the reference's vision?

5. **Produce structured output:**
   - **Schema layer** — if the reference describes a pattern that an LLM agent should follow (like Karpathy's wiki maintenance pattern), create a standalone schema file (e.g. `wiki-schema.md`) that encodes the conventions and workflows. This is the most durable artifact — it can be dropped into any LLM agent's context.
   - **Improvement roadmap** — list every idea, ordered P0-P3 with effort/impact/risk. Include a decision matrix table for clarity.
   - **Seed templates** — if the reference specifies file formats (index.md, log.md), create template stubs that the project can copy and fill.
   - **Update project metadata** — README.md, AGENTS.md, .hermes.md all need updating to document the new understanding and point to the new files.

### Prioritization Framework

When ordering improvement ideas from a reference analysis:

| Priority | Meaning | Criteria |
|----------|---------|----------|
| **P0** | Build now | Unlocks everything else. High impact, low-moderate effort. |
| **P1** | Build next | High value, moderate effort. |
| **P2** | Polish | Medium value, moderate effort. Nice-to-have. |
| **P3** | Stretch | Low effort or experimental. Defer indefinitely. |

Always include a decision matrix table (Impact × Effort × Risk) and a recommended phased roadmap.

### Pitfalls

- **Don't synthesize reference and project without reading both first.** Premature mapping produces shallow insights.
- **Don't create a new skill for the integration pattern itself** — this workflow lives under `efficient-operation` as a cross-cutting method.
- **Don't skip the schema layer.** The most valuable artifact is a standalone schema file that encodes conventions — it survives session boundaries.
- **DO load the `efficient-operation` skill at session start.** The memory instruction exists for a reason. Loading it first ensures you have the platform governance, report formatting, and tool-ladder guidance active before starting work.

### Concrete Example (this session)

See the `{private-repo-dox}` project for a worked example:
- Source: Karpathy's LLM Wiki gist → `ai-docs/sources/karpathy-llm-wiki.md`
- Schema: `wiki-schema.md` (standalone schema for LLM wiki maintenance)
- Roadmap: `ai-docs/improvements-from-karpathy.md` with 15 ideas, P0-P3, decision matrix
- Templates: `template/wiki-index.md`, `template/wiki-log.md`

## Delivering Results to the User

This section encodes the user's preferences for how final output should look and feel. These are NOT optional niceties.

### Report Content
- **Final results only.** Never include intermediate data, raw tool output, debugging info, or implementation notes in user-facing output.
- When building a multi-source tool, present three tiers in reports:
  1. **Findings** — what was actually detected (matched accounts, validated data, real URLs)
  2. **Summary** — which sources ran, pass/fail, duration
  3. **Raw queries** (optional) — only if the user explicitly asks for them. Default: hidden.
- Example: Dork queries themselves are never shown in reports — only the search results (matching pages, titles, snippets) that those queries returned.

### File Delivery
- Deliver structured reports as file attachments via `MEDIA:/absolute/path/to/file` — not inline text.
- Markdown is the preferred report format (structured, readable, portable).
- Telegram platform: use MEDIA: syntax for file delivery, not inline code blocks.

### Response Structure
- Lead with the answer/finding. Tables > paragraphs.
- No preamble before the deliverable.
- Apply corrections immediately — don't describe the planned fix, apply it and state what happened.
- When the user asks "show me the full report," generate it and attach the file — don't paste it inline.
- **Exploratory "what are my options" questions: present the full landscape first, then narrow.** When the user asks about options or alternatives (credential storage, architectures, tools), lead with a broad comparison table covering the full range, not a single recommendation. Let them drive the narrowing. Pre-judging the "best" option without showing the landscape first has been corrected as too narrow.

## Work Around Blockers

When the user gives you a green light to build something and there's a blocking dependency you can't resolve immediately (missing API key, unauthenticated CLI, uncreated account):

- **Don't stop and ask for the blocker first.** The user's preference is: build what you can, move on, flag the blocker as a separate action item.
- The pattern: acknowledge the blocker briefly, build the working thing anyway, note what's still needed at the end.
- Example from this session: gh wasn't authed. Instead of waiting, build and containerize the tool. The "push to org" step waits; the tool works today.
- Exception: if the blocker genuinely prevents building anything (no language runtime, no package manager), say so clearly and offer the minimal path to unblock.

## Building CLI Tools

When building a CLI tool from scratch for the user, use this proven pattern:

### Architecture Pattern (Modular Source + Async Runner)

```
Tool
├── pyproject.toml / CLI entry point (click)
├── src/models.py          ← Pydantic data models (input types, result types)
├── src/config.py          ← Pydantic-settings (env-prefix like RECON_, CRAWL_)
├── src/sources/
│   ├── base.py            ← Abstract BaseSource with timed_run() wrapper
│   ├── __init__.py        ← SOURCE_REGISTRY dict: {"name": SourceClass}
│   └── <domain>/          ← domain-grouped source modules (phone/, email/, web/)
├── src/reporters/         ← Output formatters (JSON, markdown, table)
└── src/utils/
    └── async_runner.py    ← ReconRunner with semaphore-based concurrency
```

**Key design decisions:**

1. **Source registry pattern** — Each data source extends `BaseSource`, is registered in `SOURCE_REGISTRY`, and returns a `SourceResult` model. Adding a new source = write a class + register it. No wiring changes needed.

2. **Async concurrency with semaphore** — `ReconRunner` uses `asyncio.Semaphore(max_concurrency)` to run all sources concurrently with backpressure. Each source runs in its own coroutine.

3. **3rd party library integration** — Use subprocess (via `asyncio.to_thread`) for tools that have their own CLIs. The subprocess approach is more reliable than trying to import and call their internal APIs. Preference: use the `toolname` binary directly (e.g. `"ignorant"`) rather than `sys.executable, "-m", "toolname"` — some packages lack `__main__.py`.

4. **Containerization** — Single-stage Docker build with `python:3.11-slim` (multi-stage adds complexity without meaningful benefit for Python CLIs). Always: `--chown=recon:recon`, non-root user, `pip install -e .` for editable installs. For Go binaries (PhoneInfoga), use `ADD https://...tar.gz /tmp/` in the Dockerfile.

5. **Environment configuration** — Use `pydantic-settings` with env prefix so all config is settable via env vars, `.env` file, or CLI args.

6. **JSON output sanitization** — Control characters from CLI tool output (raw newlines in wrapped text) can break JSON serialization. Always sanitize dork URLs and raw CLI output before storing in Pydantic models. Use `json.loads(strict=False)` as a safety net on the receiving end.

7. **Search execution via DDG Lite** — See reference `ddg-lite-search-executor.md` for the free, no-auth approach to executing search queries and returning parseable HTML results. This replaces the pattern of generating Google dork URLs without executing them.

### Verification pattern

After building:
- `docker build -t <name> .` → verify it compiles
- `docker run --rm <name> --help` → verify CLI works
- `docker run --rm <name> --email "test@example.com" --quiet --format json` → verify all sources run
- Check JSON output for successful sources vs errors

### SQLite / FTS5 for local storage

When a CLI tool needs persistent storage or full-text search, use SQLite with FTS5 (zero-infrastructure, no external services). See `references/sqlite-fts5-patterns.md` for the setup pattern: standalone FTS5 tables (not content-sync), manual DELETE/INSERT triggers, COALESCE for cross-table references, and filtered search with structured WHERE clauses.

## Multi-Agent Project Configuration

When configuring a project for multiple AI agents (Hermes, Claude Code, Cursor, Copilot), each agent reads a different root config file. Hermes loads only **one** project context file per session, checked in priority order: `.hermes.md` → `AGENTS.md` → `CLAUDE.md` → `.cursorrules`. First match wins — the rest are ignored.

**Critical implication**: cross-file delegation ("DOX protocol lives in AGENTS.md") is dead code. If `.hermes.md` exists at root, Hermes never loads AGENTS.md. Each root file must be **self-referential** (self-contained) with the full protocol baked in.

Pattern for scaffolding tools: define the shared protocol as a parameterized function `_dox_core(agent_file)`, then generate agent-specific wrappers via an `--agent` flag:

| `--agent` | Root file | Subdirectory DOX |
|-----------|-----------|------------------|
| `default` | `AGENTS.md` | `AGENTS.md` at every level |
| `hermes` | `.hermes.md` | `AGENTS.md` at child levels (Hermes progressive discovery) |
| `claude` | `CLAUDE.md` | `AGENTS.md` at child levels + `CLAUDE.md` at every subfolder |

Only `--agent default` puts AGENTS.md at root. Both `hermes` and `claude` use their agent-specific file as the **sole** root contract. Child AGENTS.md files remain as the DOX hierarchy for sub-scopes.

**Claude Code requires a full parallel hierarchy** — root `CLAUDE.md` is not enough. Every subfolder with an AGENTS.md needs its own `CLAUDE.md` that is self-referential (references CLAUDE.md, not AGENTS.md).

**Overlay/merge pattern for existing projects** — `_has_dox_protocol()` checks for `# DOX framework` marker. `_write_or_merge()` either creates fresh, appends DOX if file exists without DOX, or skips if DOX already present. Full DOX tree (ai-docs/ children) is always populated on every invocation — no manual steps.

See `references/multi-agent-project-config.md` for the full reference — Hermes priority details, what each agent reads, template-driven generation architecture, overlay/merge implementation, Claude Code parallel hierarchy, auto-initialization, idempotency, and pitfalls.

## Parallel Delegation for Data Generation

When generating bulk structured data (test fixtures, synthetic agencies, dummy datasets, multi-file test scenarios):

1. **Design the schema and structure first** — define folder layout, file formats, column standards, naming conventions before generating any data. Write a schema doc as the reference.

2. **Dispatch parallel sub-agents** via `delegate_task` with 3 concurrent workers. Each gets a self-contained context with:
   - The exact demographic/research facts needed (pre-fetched, not discovered by the subagent)
   - A specific folder path to write to
   - The EXACT list of files required (filenames, schemas, row counts, formats)
   - Hidden/special requirements clearly marked

3. **Context quality over quantity** — each subagent's context must be self-contained but concise. Include:
   - Researched data (carriers, rates, demographics) — subagents should NOT re-research
   - File count and formatting requirements
   - The owner persona details so generated data feels authentic
   - Do NOT duplicate conversation history the subagent can't see

4. **While subagents work, prepare shared assets** — schemas, profiles, README, the git structure, and any Hermes or CLI configs that wrap around the generated data.

5. **Quality-check before commit** — spot-read random files from each subagent's output. Verify CSV headers match schema, row counts are reasonable, data values are realistic.

6. **Batch-commit everything in one pass** — `git add -A && git commit` with a detailed multi-line message enumerating every agency/module produced.

## Pitfalls

- **Over-delegating**: asking Claude to "fix a typo" when `patch` would take one call. Always ask "can I do this cheaper?" first.
- **Under-delegating (company ops vs personal projects)**: THE PATTERN DEPENDS ON CONTEXT.
  - **Company operations (client work)** — When the user says "go ahead," brief the team. You are Chief of Staff. Draft code for reference is fine; deploying yourself is not.
  - **Personal projects (their ideas, tools for you to use, side builds)** — When the user says "go ahead," BUILD IT YOURSELF. The user is asking you to build. Deliver a working artifact. This session's {private-repo-profile-recon} CLI is the model: research → design → build → containerize → verify → deliver.
- **Verbose prompts to subagents**: a wall of context to Claude burns tokens on both side (prompt cache + output). Keep delegation prompts short.
- **Re-explaining context**: the user's message and the conversation history are already in your context. Don't restate them in your response or delegation prompts.
- **Using LLMs for deterministic work**: don't ask an LLM to count lines, rename symbols, or format code. Use shell tools.
- **Browser automation on cloud dashboards**: using the browser tool to manage fly.io, GCP, AWS, etc. triggers bot detection and can lock accounts. CLI-first for all platform ops unless the user explicitly asks for a live interactive session.
- **Fighting SaaS signup captchas**: When signing up for new SaaS accounts (Supabase, Clerk, Resend, Sentry, etc.), automated browser signups hit hCaptcha or reCAPTCHA and will fail every time. Don't spend multiple turns trying different approaches — identify the captcha constraint immediately, then give the user a clear one-click list of 5-6 services to sign up via GitHub OAuth in their own browser. State the time commitment (~12 minutes) and exactly what API keys to send back. This preserves the async relationship and avoids wasted automation turns.
- **Tilde expansion under Hermes profiles**: `$HOME` points to the profile directory, not `{user_home}`. Any CLI that resolves `~` at runtime (common with Rust/Go tools like himalaya) will find configs/venvs at the wrong path. See `references/hermes-profile-path-workaround.md` for the fix and affected tool list. Always use absolute `{user_home}/...` paths in `terminal()` calls.
- **Fine-grained GitHub PATs can't accept org invites**: When a task requires accepting an org membership invitation and the token is a fine-grained PAT, the API will return 403. Flag this to the user rather than spending turns trying to work around it. See `references/fine-grained-pat-limitations.md` for details.
- **Cron `no_agent` is set-once**: Toggling `no_agent=true` to agent-driven (or vice versa) via `cronjob(action='update')` is silently ignored — the field persists from creation. To switch mode, delete the job (`cronjob(action='remove', job_id=...)`) and recreate with the desired setting. Verify via `last_status` is none of `ok/error/timeout` on the old job before removal.
- **Cron `repeat` defaults to `once`**: When creating a recurring cron, `repeat` must be explicitly set to `0` (integer zero) or the job defaults to `repeat: once` and self-terminates after its first run. Always verify `repeat` after creation via `cronjob(action='list')` and update with `cronjob(action='update', repeat=0)` if needed.
- **Don't assume shared infrastructure is available for new projects.** Company infrastructure (Fly.io, Supabase, etc.) belongs to specific business entities (e.g., an agency). Don't propose piggybacking on them for personal projects or unrelated tools unless the user explicitly offers. Always ask or default to zero-infrastructure approaches first.