# Multi-Agent Project Configuration

When a project needs to work with multiple AI agents (Hermes, Claude Code, Cursor, Copilot), each agent reads a different root config file. Getting this wrong means an agent silently ignores your instructions — there's no error, it just never sees the context.

## The Priority Problem (Hermes)

Hermes loads **only one** project context file per session, checked in order:

```
.hermes.md → AGENTS.md → CLAUDE.md → .cursorrules
```

**First match wins, rest are ignored.** This means:

- If `.hermes.md` exists at root, Hermes never reads `AGENTS.md` or `CLAUDE.md`
- A delegation line like "DOX protocol lives in AGENTS.md" in `.hermes.md` is **dead code** — AGENTS.md was never loaded
- Subdirectory AGENTS.md files are still progressively discovered as the agent navigates — but only the root-level loading is blocked

### The Claude Code Challenge: Subfolder Hierarchy

Claude Code reads root `CLAUDE.md` at startup. But when it navigates into subdirectories (e.g., `ai-docs/`, `src/`), it encounters `AGENTS.md` files there — which it **ignores**. Claude Code does NOT read AGENTS.md at any level.

**Fix**: Generate a parallel `CLAUDE.md` at every subfolder that has an `AGENTS.md`. Each subfolder `CLAUDE.md` must be self-referential (references CLAUDE.md, not AGENTS.md):

```
project/
├── CLAUDE.md                    ← root: self-contained DOX protocol
├── ai-docs/
│   ├── AGENTS.md                ← DOX child contract
│   ├── CLAUDE.md                ← Claude Code: self-referential
│   ├── plans/
│   │   ├── AGENTS.md
│   │   └── CLAUDE.md            ← Claude Code: self-referential
│   └── tasks/
│       ├── AGENTS.md
│       └── CLAUDE.md            ← Claude Code: self-referential
```

Each subfolder `CLAUDE.md` wraps the same shared protocol content but with CLAUDE.md references instead of AGENTS.md. The root `CLAUDE.md` should include a **Subdirectory Navigation** table telling Claude Code exactly which child CLAUDE.md files to read when it changes directory.

## The Parameterized Core Pattern (DOX_CORE → _dox_core())

A static `DOX_CORE` constant works when the protocol only references one file type. But when you need both AGENTS.md-referencing and CLAUDE.md-referencing versions, use a **function** instead:

```python
def _dox_core(agent_file: str) -> str:
    """Generate DOX protocol with references to agent_file name."""
    child_file = agent_file                    # "AGENTS.md" or "CLAUDE.md"
    child_plural = agent_file + " files"
    root_ref = f"root {agent_file}"

    return f"""# DOX framework
...
- {child_file} files are binding work contracts for their subtrees
...
1. Read the {root_ref}
...
See `ai-docs/plans/{child_file}` for the plan contract
"""
```

Then call it with the right argument per generator:
- `make_hermes_md()` → `_dox_core("AGENTS.md")` — Hermes uses AGENTS.md for subfolder discovery
- `make_agents_md()` → `_dox_core("AGENTS.md")` — canonical AGENTS.md
- `make_root_claude_md()` → `_dox_core("CLAUDE.md")` — Claude Code uses CLAUDE.md for subfolder discovery
- `make_claude_ai_docs_md()` → `_dox_core("CLAUDE.md")` — Claude Code subfolder

This keeps a single source of truth for the protocol text while producing correct file references per agent.

Each root config file must be **self-referential** (self-contained) — the full protocol content baked in, not delegated:

```
project-root/
├── .hermes.md    ← Hermes: full protocol + runtime shortcuts (self-contained)
├── AGENTS.md     ← Others: full protocol + Child DOX Index (self-contained)
├── CLAUDE.md     ← Claude Code: full protocol (self-contained)
```

Each file is independently complete. No one file depends on another for its instructions.

## The Template-Driven Generation Pattern

Maintaining N copies of the same protocol across N agent files is a maintenance burden. The cleanest approach: one source of truth in code that generates agent-specific wrappers.

### CLI Interface

```
dox-scaffold init <name> [description] [--agent <type>] [--overlay]
```

| `--agent` | Root file generated | Subdirectory DOX |
|-----------|-------------------|------------------|
| `default` | `AGENTS.md` | `AGENTS.md` at every level |
| `hermes` | `.hermes.md` | `AGENTS.md` at child levels (Hermes progressive discovery) |
| `claude` | `CLAUDE.md` | `AGENTS.md` at child levels + `CLAUDE.md` at every subfolder level |

**Key design rule**: only `--agent default` puts `AGENTS.md` at root. Both `hermes` and `claude` use their agent-specific file as the **sole** root contract. No canonical AGENTS.md coexists at root for agent-specific modes. Child AGENTS.md files remain as the DOX hierarchy for sub-scopes.

### DOX Overlay Pattern (Existing Projects)

When adding DOX structure to an existing project (the `--overlay` flag), three cases per root file:

| File state | Behavior |
|------------|----------|
| Doesn't exist | **Created** fresh with full DOX protocol |
| Exists, no `# DOX framework` signaturer | **Appended** — user's content preserved at top, clear `---` separator, `## DOX Framework (appended by dox-scaffold)` section added |
| Exists, has `# DOX framework` signature | **Skipped** — already DOX-aware, no changes |

Implementation:
```python
DOX_SIGNATURE = "# DOX framework"

def _has_dox_protocol(content: str) -> bool:
    return DOX_SIGNATURE in content

def _write_or_merge(path: Path, content: str, label: str) -> str:
    if not path.exists():
        path.write_text(content)
        return "created"
    existing = path.read_text()
    if _has_dox_protocol(existing):
        return "skipped"
    # Append with clear separator
    append_block = (
        f"## DOX Framework (appended by dox-scaffold)\n\n"
        f"..."
        f"{content}"
    )
    path.write_text(existing.rstrip() + "\n\n---\n\n" + append_block)
    return "merged"
```

### Auto-Initialization (Full DOX Tree)

Both new-project (`init`) and overlay (`--overlay`) modes **always populate the full DOX tree**:

```
project-root/
├── <root-contract>        ← agent-specific
├── ai-docs/
│   ├── AGENTS.md          ← DOX child contract
│   ├── plans/AGENTS.md    ← Plan format + template
│   └── tasks/AGENTS.md    ← Task lifecycle + template
```

No manual steps needed. The CLI ensures all DOX structure files exist at every level on every invocation.

### Shell CLI Limitations

The shell-based CLI (`bin/dox-scaffold`) can only generate the default AGENTS.md template. For `--agent hermes` or `--agent claude` or `--overlay`, it prints a clear note directing the user to the Python CLI:

```
pip install dox-scaffold
dox-scaffold init my-app "Description" --agent hermes
```

This keeps the shell wrapper as a low-friction entry point while funneling advanced features to the Python version.

### What Each Agent Reads

| Agent | Loads at root | Where it looks |
|-------|---------------|----------------|
| **Hermes Agent** | `.hermes.md` (highest priority) | CWD → git root |
| **Claude Code** | `CLAUDE.md` | Project root, or `.claude/CLAUDE.md` |
| **Cursor** | `.cursorrules` | Project root |
| **Copilot** | `.github/copilot-instructions.md` | `.github/` subdirectory |

### Idempotency

Overlay mode is idempotent. Running `dox-scaffold init <dir> --agent hermes --overlay` twice produces the same result:
- **First run**: files created (or appended if non-DOX root exists)
- **Second run**: all files skipped (they now have the `# DOX framework` signature)

This makes overlay safe for CI/CD, onboarding scripts, and repeated setup commands.

### Reference Implementation

See `dox-scaffold` for a worked example:
- `src/dox_scaffold/__init__.py` — `_dox_core()` function, agent generators, `--agent`/`--overlay` flags, `_write_or_merge()` / `_has_dox_protocol()` overlay logic
- `bin/dox-scaffold` — shell wrapper with fallback note for non-default agents
- Three root files all self-contained but sharing the same protocol core
- Claude subfolder generators: `make_claude_ai_docs_md()`, `make_claude_plans_md()`, `make_claude_tasks_md()`

### Hermes Skill Packaging

When distributing a scaffolding tool that generates agent-aware projects, include a Hermes skill in the repo:

```
repo-root/
├── skills/<tool-name>/
│   ├── SKILL.md                    ← skill metadata + usage
│   └── scripts/scaffold.py         ← convenience wrapper (optional)
```

The SKILL.md should:
- Default usage examples to `--agent hermes` so Hermes users get the right root file
- Document the multi-agent landscape (who reads what)
- Include a pitfalls section about the priority system
- Mention `--overlay` for adding DOX to existing projects
- Reference the wrapper script if one exists

Installation for the user:
```bash
cp -r skills/<tool-name> ~/.hermes/skills/software-development/
```

### Pitfalls

- **Don't use cross-file delegation** — If `.hermes.md` says "see AGENTS.md", Hermes will obey the instruction to read it (via `read_file` on turn 1), but the protocol ends up in conversation context, not system prompt. Worse for prompt caching. **Bake the protocol in directly.**
- **Don't assume one file works for all agents** — Each agent has its own discovery path. A file in `agents/` subdirectory is invisible to every agent at root level.
- **Version-lock your generators** — When updating the shared `_dox_core()` function, regenerate all scaffolded project root files. Stale root files mean stale instructions that silently misdirect agents.
- **The shell wrapper can't do it all** — Shell-based scaffolding tools (Bash, npm scripts) can only copy static template files. For dynamic root-file generation per agent or overlay mode, the canonical CLI needs Python (or equivalent) with template logic.
- **Child docs don't carry the DOX signature** — `ai-docs/AGENTS.md` child docs use `# Purpose` as their heading, not `# DOX framework`. Overlay mode skips existing child docs rather than checking for DOX — they have their own DOX-aware structure that shouldn't be duplicated.
- **Don't confuse Hermes startup load with subdirectory discovery** — The priority system (`.hermes.md` → `AGENTS.md` → ...) only controls what's loaded at **session start** into system prompt. Subdirectory AGENTS.md files are still progressively discovered as Hermes navigates. The `.hermes.md` at root points to AGENTS.md for these child scopes, which works correctly.
