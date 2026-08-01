---
name: special-projects-manager
description: "Manage the user's special projects — YAML frontmatter stored in PROGRESS.md (not README.md), with append-only progress logs and the progressive disclosure reading pattern. Governs project creation, recall, updates, and catalog maintenance."
version: 2.0.0
author: Alpha
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [projects, tracking, productivity, obsidian, frontmatter, progressive-disclosure]
    category: productivity
---

# Special Projects Manager

System for tracking the user's personal and company special projects. Each project lives in its own subdirectory under `~/{profile}/projects/` with two standardized files.

## Directory Structure

```
~/{profile}/projects/
├── CATALOG.md                          ← Master dashboard (auto-maintained)
├── templates/                          ← Template directory
│   ├── README.md
│   └── PROGRESS.md
├── <project-name>/                     ← Per-project subdirectory
│   ├── README.md                       ← Project overview (human-readable, no frontmatter)
│   └── PROGRESS.md                     ← YAML frontmatter + append-only activity log
└── ...
```

## README.md — Human-Readable Overview (No Frontmatter)

README.md is pure markdown — no YAML frontmatter. It describes *what* the project is and *where* it stands, for human readers and standard markdown renderers.

Sections:
- `## One-Liner` — single-sentence project pitch
- `## Description` — a few paragraphs explaining the project
- `## Goals` — task list of goals
- `## Key Links & Locations` — code paths, URLs, infra
- `## Current State` — brief status paragraph

## PROGRESS.md — Frontmatter Schema

Every project PROGRESS.md starts with YAML frontmatter (Obsidian-compatible) at the very top of the file, before the log content:

```yaml
---
title: "Project Name"
status: active            # active | paused | idea | archived | completed
priority: p2              # p0 (urgent fire) | p1 (important) | p2 (nice-to-have) | p3 (eventual)
phase: research           # research | design | build | test | deploy | iterate | deferred
created: 2026-07-19
updated: 2026-07-20
tags: [tag1, tag2]
repo: null                # GitHub repo URL (null if none)
area: personal            # personal | company | shared
---
```

### Status Values

Projects have one of these internal status values (stored in YAML frontmatter). They display in this order with the corresponding emoji:

| # | Value | Emoji | Meaning | Displayed |
|---|-------|-------|---------|-----------|
| 1 | `idea` | ⚪️ | New project idea requiring research/planning before it can be worked on. Placeholder for a concept. | Always |
| 2 | `active` | 🟢 | Active project, in progress | Always |
| 3 | `blocked` | ⚠️ | User attention required — cannot progress without user action | Always |
| 4 | `paused` | 🟡 | Project is paused — user decided not to prioritize for now | Always |
| 5 | `broken` | 🔴 | Major issue or error. Risk to completion, timeline/date, or a break issue in the project | Always |
| 6 | `archived` | 🗄 | Completed or discontinued — no longer actively tracked. Show count by default, only list if reviewing the archive | Count only |

### Priority Values

Available priority levels, displayed as `P0`–`P3`:

| Value | Label | Meaning | When to use |
|-------|-------|---------|-------------|
| `p0` | 🔥 Critical | Actively blocking something else, hard deadline imminent | Pipeline down, launch blocker, urgent fix |
| `p1` | ⚡ High | Important — high value, should work on soon | Core feature, client-facing, time-sensitive |
| `p2` | 📋 Medium | Nice-to-have — work on when there's time | Enhancement, polish, non-critical feature |
| `p3` | 🗃️ Low | Eventual — someday / maybe | Idea backlog, stretch goal, low-impact |

### Phase Values

Available phase values, ordered roughly by project lifecycle:

| Value | Meaning | When to use |
|-------|---------|-------------|
| `research` | Exploring options, gathering information, defining scope | Early stage, reading/learning, evaluating approaches |
| `design` | Architecting solution, planning approach, prototyping | Whiteboarding, schema design, tech selection |
| `build` | Active construction / development | Writing code, building infrastructure, creating assets |
| `test` | Testing, validation, quality assurance | Running tests, fixing bugs, user acceptance |
| `deploy` | Shipping, releasing, rolling out | CI/CD, launch, migration, going live |
| `iterate` | Built and live — now improving | Post-launch enhancements, v2 thinking, performance tuning |
| `maintain` | Live project, ongoing care | Active project that just needs monitoring, not feature work |
| `deferred` | Not actively working (neutral) | Put aside intentionally, not blocked, just not now |
| `stalled` | Blocked and unable to progress (see blocker) | Hitting a dependency, waiting on external factor |

### Priority + Phase in Status Column

When displaying a project row, if phase is `stalled` or `deferred`, append the phase label after the priority:

| Status | Project | Pri | Phase |
|--------|---------|-----|-------|
| 🟢 | [Example](link) | P2 | Build |
| 🟡 | [Example](link) | P2 | Deferred |
| ⚠️ | [Example](link) | P1 ⚡ | Stalled |

## PROGRESS.md — Append-Only Log Format (Below Frontmatter)

After the closing `---` of the YAML frontmatter, the rest of PROGRESS.md is the append-only log. Each entry is a **date header** followed by tagged lines. Tags enable deterministic parsing.

### Tag Taxonomy

| Tag | Purpose | When to use |
|-----|---------|-------------|
| `[goal]` | Project goal definition / refinement | Defining or updating what success looks like |
| `[decision]` | Key decision with rationale | Chose X over Y because... |
| `[action]` | Action completed | Built X, deployed Y, shipped Z |
| `[todo]` | Action still needed | Next steps, follow-ups |
| `[blocker]` | Blocker encountered | Something blocking progress |
| `[progress]` | General progress update | Status check-in, milestone reached |
| `[status]` | Status change | Active → Paused, Paused → Active, etc. |
| `[question]` | Open question | Need input from the user or someone else |
| `[note]` | Brain dump / context | Free-form thoughts |
| `[reference]` | Reference link or resource | Useful link, doc, or resource |

### Log Entry Format

```markdown
## 2026-07-20

[decision] Switch from DuckDuckGo to SearXNG for search backend
  Rationale: DDG rate-limiting was unreliable. SearXNG self-hosted gives consistent results.

[action] Rebuilt Dockerfile with python:3.11-slim base
  Result: Image size dropped from 420MB to 185MB.

[blocker] PhoneInfoga Google dorks hitting CAPTCHA
  Impact: 4 of 6 dork categories returning empty. Need alternative approach.

[todo] Add HIBP API integration
  Priority: p2 — nice-to-have. Needs API key.
```

Rules:
- Each entry starts with a `## YYYY-MM-DD` header
- Tags are on their own line, colon-separated from the description
- Additional context (rationale, impact, result) is indented under the tag line
- Append new entries at the TOP of the file (newest first)

## Progressive Disclosure Reading Pattern

When recalling project state:

1. **Read CATALOG.md** — see what's active, paused, ideas at a glance
2. **Read `projects/<name>/PROGRESS.md` (first ~15 lines)** — parse YAML frontmatter for status/priority/phase/metadata
3. **Read `projects/<name>/README.md`** — human-readable overview, goals, current state
4. **Tail last 10-20 lines of PROGRESS.md** (below the frontmatter) — see latest actions, decisions, blockers, next todos
5. **Tail deeper into PROGRESS.md** only when you need history on a specific decision or action

## Workflow: Creating a New Project

1. Copy `templates/README.md` and `templates/PROGRESS.md` into `projects/<name>/`
2. Fill frontmatter fields in `PROGRESS.md` (status, priority, phase, etc.)
3. Write a `## One-Liner` and `## Description` section in `README.md`
4. If context exists, seed PROGRESS.md log with any prior decisions/actions
5. Add the entry to CATALOG.md (link to the README, status emoji, priority, last updated, one-liner)
6. **Scaffold the actual code repo** — choose the right approach based on project type:
   - **DOX-framework projects** (CLI tools, web apps, packages): Use `dox-scaffold init <name> "description" --agent hermes` to generate a DOX-framework project at `~/projects/<name>/`. Install dox-scaffold first: `pip install dox-scaffold` (the shell script at `./bin/dox-scaffold` does NOT support `--agent`).
   - **Non-DOX projects** (skill repositories, config repos, documentation sites, data repos): Scaffold the directory structure directly with `mkdir -p`, `write_file`, and `git init`. No dox-scaffold needed.
   - Verify the project landed at the expected path (CWD-dependent for dox-scaffold).
   - After scaffold, update the tracking README.md's `## Key Links & Locations` to point to the code repo.
7. **Write the first plan** — for DOX projects, create `ai-docs/plans/P001-<name>-phases.md` in the code repo. For non-DOX projects, skip the `ai-docs/plans/` directory unless the project architecture genuinely needs phased planning docs.

## Workflow: Recording Progress

1. Open the project's `PROGRESS.md`
2. If today's date header doesn't exist, add one at the TOP (after the frontmatter)
3. Add entries under today with appropriate tags
4. Update `updated` field in PROGRESS.md frontmatter
5. Update `phase` / `status` / `priority` in PROGRESS.md frontmatter if changed

## Workflow: Archiving a Project

When a project is complete (shipped, delivered, or abandoned):

1. Update `status: archived` and `updated` in PROGRESS.md frontmatter
2. Add a closing `[status]` entry (e.g. `Active → Archived — project complete`)
3. Log `[action]` entries for final deliverables
4. Move the CATALOG.md row from its status section to a `## Archived` section
5. Update the catalog's frontmatter `updated:` timestamp

### Archiving with Skill Bundle

When a project's output is a reusable tool or script, bundle it into a Hermes skill before archiving:

1. **Identify or create the skill** — either extend an existing skill or create a new one
2. **Copy the tool into the skill's `scripts/` directory:**
   `cp project/script.py skills/<category>/<skill-name>/scripts/`
3. **Update profile-level wrappers** (`~/{profile}/scripts/`) to point to the skill copy
4. **Update SKILL.md:**
   - Remove `project:` from frontmatter (skill is now self-contained)
   - Add a `## Script (Bundled)` section with the new path
   - Point usage examples at the profile wrapper, not the old project path
5. **Verify** — run the bundled script and confirm it works
6. **Archive the project** per normal workflow, add a `[reference]` entry linking to the skill

**Rationale:** The project directory freezes as a historical record; the working artifact lives in the skill system where future sessions find it.

## Workflow: Reading Project State (for Alpha)

When asked "what's up with X" or when starting a session:

1. Read CATALOG.md for full picture
2. For each active project, read PROGRESS.md (parse frontmatter) + tail -5 PROGRESS.md log
3. Optionally read README.md for detailed description and goals
4. **Cross-validate stale entries** — if a project's "Last Updated" is more than 3-4 days old, especially with status "Idea" or "Research," run `session_search` on the project name and check for a real code repo at the path listed (or `~/projects/<name>/`). The tracking files may be stale if work happened outside this project directory.
5. Summarize to the user: current phase, last action, any blockers needing their input

## CATALOG.md Format

CATALOG.md starts with minimal YAML frontmatter (just the `updated` timestamp), then standard markdown:

```yaml
---
updated: 2026-07-20
---
```

```markdown
# Project Catalog

Managed by the user's personal assistant & special projects manager.

## At a Glance

| Status | Project | Priority | Phase | Last Updated | One-Liner |
|--------|---------|----------|-------|-------------|-----------|
| 🟢 Active | [dox-scaffold](dox-scaffold/) | P2 | Deploy | 2026-07-19 | Personal scaffolding CLI |
| ⚪ Idea | [Self-Learning Repo](self-learning-repo/) | P3 | Research | 2026-07-19 | Autonomous daily wiki |

### Status Legend
| Symbol | Meaning |
|--------|---------|
| 🟢 | Active |
| 🟡 | Paused |
| ⚪ | Idea |
| 🔴 | Archived |
| ✅ | Completed |
```

## Project Review Output Format (Telegram)

When the user asks for a project review or status update, use this defined output format. All projects in a single table — the emoji in the Status column communicates the state at a glance.

### Review Header

```
📋 **Special Projects Review — YYYY-MM-DD**
```

### Single Table (All Projects)

Sorted by status order (⚪️ → 🟢 → ⚠️ → 🟡 → 🔴 → 🗄), then by priority within each group. 🗄 (archived) projects show count only by default — only list them if explicitly reviewing the archive.

```
| Status | Project | Pri | Phase | 🔄 Last Action |
|--------|---------|-----|-------|----------------|
| ⚪️ | [Self-Learning Repo](link) | P3 | Research | Jul 19 — Needs seed topic |
| 🟢 | [Profile Recon CLI](link) | P2 | Iterate | Jul 20 — Added SearXNG backend |
| ⚠️ | [Some Project](link) | P1 | Build | Jul 20 — Waiting on API key |
| 🟡 | [Old Project](link) | P2 | Deferred | Jul 15 — On hold |
| 🔴 | [Broken Project](link) | P1 | Build | Jul 20 — CI pipeline failing |
```

```
| Status | Project | Pri | Phase | 🔄 Last Action |
|--------|---------|-----|-------|----------------|
| 🟢 | [Nous Portal Credits](link) | P2 | Build | Jul 20 — Built CLI, cron live |
| 🟢 | [Profile Recon CLI](link) | P2 | Iterate | Jul 20 — Added SearXNG backend |
| ✅ | [GitHub Org Setup](link) | P1 | Deploy | Jul 20 — Org created by the user |
| ⚪ | [Self-Learning Repo](link) | P3 | Research | Jul 19 — Needs seed topic |
```

### Blocker Section (if any)

If any project has a `[blocker]` tag in the latest PROGRESS.md entries:

```
⚠️ **Needs Your Input**

- **Project Name** — Blocker description
```

### Summary Line

Count by emoji, status order, archives counted but not listed:

```
📊 **4 🟢 · 0 ⚠️ · 0 🟡 · 0 🔴 · 3 ⚪️ · 1 🗄**
```

```
📊 **4 active · 1 completed · 3 ideas · 0 paused**
```

### Full Example

```
📋 **Special Projects Review — Jul 20**

| Status | Project | Pri | Phase | 🔄 Last Action |
|--------|---------|-----|-------|----------------|
| ⚪️ | [Self-Learning Repo](self-learning-repo/) | P3 | Research | Jul 19 — Needs seed topic |
| ⚪️ | [Artifact Builder](artifact-builder/) | P3 | Research | Jul 19 — Needs scope |
| 🟢 | [Nous Portal Credits](nous-credits/) | P2 | Build | Jul 20 — CLI built, cron live |
| 🟢 | {project} | P2 | Research | Jul 19 — Defining MVP |
| 🟢 | [dox-scaffold](dox-scaffold/) | P2 | Iterate | Jul 19 — Built on GitHub |
| 🟢 | [Profile Recon CLI]({private-repo-profile-recon}-cli/) | P2 | Iterate | Jul 20 — SearXNG live |

⚠️ **Needs Your Input**
- **Some Project** — Waiting on API key

📊 **4 🟢 · 0 ⚠️ · 0 🟡 · 0 🔴 · 3 ⚪️ · 1 🗄**
```

### How to Generate (for Alpha)

1. **Read CATALOG.md** — gets all project names, statuses, priorities
2. **Batch-read PROGRESS.md files** — use `execute_code` to read all projects' PROGRESS.md frontmatter + tails in a single call (parallel reads, far fewer turns than reading each individually)
3. Compile into the single table above, sorted by status then priority
4. Check for `[blocker]` and `[question]` tags in the latest PROGRESS.md entries — those go in "Needs Your Input"
5. Add summary line at the end

For context on ideas or inactive projects, read README.md on demand — don't batch-read everything at once.

## Pitfalls

- **Don't inline full PROGRESS.md** — progressive disclosure means reading only what's needed
- **Don't forget to update `updated` timestamp in PROGRESS.md frontmatter** — stale dates mislead the catalog view
- **Use the right tag** — `[action]` for completed work, `[todo]` for pending. Mixing them undermines deterministic parsing.
- **Never rewrite/truncate PROGRESS.md** — it's append-only append-at-top. Preserves full decision history.
- **No browser automation** for project management — all CLI/file-based.
- **When status changes to `completed` or `archived`**, move the project entry to a separate section in CATALOG.md, don't remove it.
- **CATALOG.md table formatting is fragile** — patch operations that replace table rows must keep exact pipe alignment. A `|` vs `||` mismatch breaks the table rendering. After any CATALOG.md edit, verify the table renders by re-reading the file.
- **CATALOG.md and README.md can become stale** — the tracking files only reflect what was logged in the PROGRESS.md. If work happened in the code repo or another session without logging (e.g. initial scaffolding, repo creation, commits), the catalog will show the project as "Idea / Research" when it's actually "Build." Always cross-validate by session_search and checking the actual repo path for projects not updated in 3+ days.
- **dox-scaffold projects land in CWD** — running `dox-scaffold init <name>` from inside another repo (e.g. the dox-scaffold repo itself) creates the project nested there. Always run from the parent `~/projects/` directory, or move the scaffolded project afterward.

## Related Patterns

For knowledge wikis and multi-folder information bases, see the
[AGENTS.md Progressive Disclosure Pattern](references/agents-progressive-disclosure-pattern.md)
reference — an alternative to flat `index.md` catalogs that uses structured
frontmatter and folder-level AGENTS.md files for navigation and querying.
