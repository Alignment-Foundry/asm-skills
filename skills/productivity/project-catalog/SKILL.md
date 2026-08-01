---
name: project-catalog
description: "Manage the user's project catalog — create, update, archive project entries"
version: 1.2.0
author: Alpha
---

# Project Catalog Management

Template for managing the user's project catalog at `~/{profile}/projects/`.

## When to Create vs When to Just Do

- **Create a project entry** when the user talks about an idea, concept, or new initiative — even at the ⚪ Idea stage. The catalog is a scratchpad for capturing every concept so nothing gets lost.
- **Do NOT create project entries** for one-off tasks the user asks you to execute (run a command, test a thing, answer a question). Those belong in conversation history.
- **Threshold for project-worthy**: if the user mentions a concept twice in one session, or if it would take 10+ tool calls to complete, it's a project.

## How to Transition an Idea to Active

When the user says "let's go with" or "build this" on an ⚪ Idea:
1. Move status to 🟢 Active in both PROGRESS.md frontmatter and CATALOG.md
2. Log the transition and add concrete action items to PROGRESS.md
3. Build the minimum viable thing immediately — don't scope-creep in the catalog entry
4. After building, update the entry with built artifacts (paths, Docker images, URLs)

## Core Principles

- **When the user mentions a new idea, create the entry immediately** — don't wait to be asked twice. The entry is lightweight; it can be updated.
- **When creating entries for multiple projects mentioned at once**, create ALL files first, then present the board for confirmation. Batch the writes.
- **Always confirm statuses with the user** — your initial assessment is a draft. the user may correct ⚪ Idea → 🟢 Active (e.g. "we're in alpha"), or you may need to ask. Use the brief summary format at the end to let the user sign off.
- **External blockers (waiting on the user) go to 🟡 Paused** with clear Action Items for the user listed in the project file. Never leave a blocked project at Active.

## Status Definitions

| Status | When to use |
|--------|-------------|
| 🟢 Active | Being worked on now. Includes projects with working code, running alpha/beta versions. |
| 🟡 Paused | Blocked on external input (name, API key, decision). Clear Action Items listed in project file. |
| ⚪ Idea | Concept stage. Nothing built yet. |
| 🗄 Archived | Completed (shipped, done) or abandoned (no longer pursuing). |

## Workflow

### Creating a new project entry

1. Copy `templates/README.md` and `templates/PROGRESS.md` into a new subdirectory (e.g. `projects/my-idea-name/`)
2. Fill in: status, created date, description, key locations, tags
3. Add to CATALOG.md under the appropriate status section
4. **Present the full board to the user for confirmation** — statuses are drafts until he signs off

### Creating entries from multiple ideas at once

1. Create ALL project files in parallel (single batch of write_file calls)
2. Update CATALOG.md with all entries
3. Present a compact table of all projects with statuses
4. Let the user correct any statuses in one pass

### Updating a project

1. Read the project file
2. Update status, last activity, add notes/history entry
3. Update CATALOG.md if status changed sections

### Archiving

1. Set status to 🗄 Archived
2. Add closing note to PROGRESS.md log with final actions taken
3. Move entry to Archived section in CATALOG.md
4. **If the project produced a reusable script/tool:** bundle it into a skill first (copy script into the skill's `scripts/` dir, update wrappers) so the cron or downstream consumers still work. Then archive the project.

### Handling projects with external blockers

1. Create the project file with status 🟡 Paused
2. Include a clearly named "Action Items" section listing what the user needs to provide
3. Add specific, numbered action items with checkboxes
4. In CATALOG.md, place under the 🟡 Paused section

## File Structure

```text
~/{profile}/projects/
├── CATALOG.md               ← Master index (all projects by status)
├── templates/
│   ├── README.md             ← Template: human-readable overview (no frontmatter)
│   └── PROGRESS.md           ← Template: YAML frontmatter + append-only log
└── <project-name>/
    ├── README.md             ← Project overview (human-readable, no frontmatter)
    └── PROGRESS.md           ← Frontmatter schema per special-projects-manager
```

**NOTE:** This skill handles *lifecycle management* (when to create/update/archive). The *file format* (frontmatter schema, tag taxonomy, append-only log format) is governed by the `special-projects-manager` skill, which is canonical. See `references/overlap-note.md` for details.

## GitHub Org Projects (Special Pattern)

When the user asks to set up a GitHub org for collaboration:

### ⚠️ Fine-Grained PAT Limitation

If the gh token is a fine-grained PAT (`github_pat_...`), many org-level operations are blocked:
- **Cannot accept org invites** via API — the user must click the invite link in browser
- **Cannot create repos under the org** — `Resource not accessible` / `You need admin access`
- **Cannot transfer repos to the org** — `Resource not accessible by personal access token`

For org-level operations, fall back to **manual repo creation by the user**: he creates the repo in the browser, then we push content to it (add as a secondary remote, push).

See `references/fine-grained-pat-limitations.md` in the `efficient-operation` skill for full details.

### Workflow

1. Ask for the org name first → create entry at 🟡 Paused
2. Once name is confirmed → check `gh auth status` IMMEDIATELY
3. If gh is not authed → tell the user a token is needed (link to generate one)
4. GitHub orgs CANNOT be created via CLI or API — the user must create via web UI at https://github.com/account/organizations/new?plan=free
5. If token is fine-grained: ask the user to click the invite link in browser at `https://github.com/orgs/ORG_NAME/invitation?via_email=1`
6. **Creating repos under the org (preferred path when fine-grained PAT):**
   - the user creates the repo manually in browser at `github.com/orgs/ORG_NAME/repositories/new` — make it private, no README/gitignore/license (we push existing content)
   - Then push existing content: `git remote add org https://github.com/ORG_NAME/repo-name.git && git push org main`
7. If classic PAT with sufficient scopes is available:
   - `gh repo create ORG_NAME/repo-name --public --clone`
   - Or use API: `POST /orgs/ORG_NAME/repos`
8. Set up branch protection, issue templates, and org-level defaults after repos exist

## Reference Examples

- `references/session-example-{private-repo-profile-recon}.md` — Full lifecycle of a project from ⚪ Idea → 🟢 Active with built artifact in one session

## When to update

- the user says "I want to start X" or has a new idea
- the user mentions a concept twice (it's worth tracking)
- the user asks me to work on something substantial (not one-off tasks)

## Status management during active work

When a project transitions from idea → building → delivered:

1. **Update status immediately** when work begins (⚪ Idea → 🟢 Active) — don't wait until completion
2. **Update status when paused** — set 🟡 Paused with a note on what's blocking or pending
3. **Update Last Activity date** on every status change
4. **Expand the Notes section** with progress bullets as work happens (✅ done items, 🔄 pending items)
5. **Move the CATALOG.md entry** to the correct status section immediately

This keeps the catalog accurate in real time, not just at milestone boundaries.

## When to update

- After working on a project, log what happened
- Status changes (active ↔ paused ↔ archived)
- New notes or decisions recorded

## Pitfalls

- **Don't let external blockers stop forward progress.** When the user gives a green light to build and you hit a dependency you can't resolve (missing API key, unauthed CLI, uncreated account), don't stop and ask. Build what you can, note the blocker as a separate action item, deliver working output. Flag the blocker at the end. Example: "gh not authed" → build the tool anyway, note "push to org" as a follow-up. the user will tell you when he wants the blocker resolved.
- **Don't over-classify statuses.** If a project has working code but you haven't deployed it, it's 🟢 Active, not ⚪ Idea. Move to Active when there's code, even if it's alpha/unreleased.
