# Hermes Cron Job Patterns

Quick reference for the `cronjob` tool — the only tool needed for scheduling.

## Quick Reference

```python
# Agent-mode job (with LLM reasoning)
cronjob(action="create", schedule="0 2 * * *", name="Job Name",
        model={"model": "deepseek/deepseek-v4-flash", "provider": "nous"},
        deliver="local",
        prompt="Your self-contained instructions here. The agent will load tools and execute.")

# Script-only job (no LLM, zero tokens, pure shell)
cronjob(action="create", schedule="15 2 * * *", name="Script Job",
        no_agent=True, script="script-name.sh", deliver="local")

# One-shot (ISO timestamp future date)
cronjob(action="create", schedule="2026-07-05T03:00:00", name="One Time",
        prompt="Do one thing and stop.")
```

## Lifecycle

| Action | Syntax |
|--------|--------|
| List | `cronjob(action="list")` |
| Pause | `cronjob(action="pause", job_id="...")` |
| Resume | `cronjob(action="resume", job_id="...")` |
| Remove | `cronjob(action="remove", job_id="...")` |
| Manual trigger | `cronjob(action="run", job_id="...")` |
| Update schedule | `cronjob(action="update", job_id="...", schedule="0 3 * * *")` |

## Schedule Formats

| Format | Example | Meaning |
|--------|---------|---------|
| Duration | `"30m"` | Every 30 minutes |
| Human phrase | `"every 2h"`, `"every Monday 9am"` | Natural language |
| Cron expression | `"0 2 * * *"` | 5-field cron (min hour day mon dow) |
| ISO timestamp | `"2026-07-05T03:00:00"` | One-shot future date |

**Timezone:** Runs in the server's local timezone. Check with `date +%Z` / `timedatectl show --property=Timezone`. If server is America/New_York, `0 2 * * *` = 2:00AM ET.

## Key Parameters

| Parameter | Purpose |
|-----------|---------|
| `model` | Dict `{"model": "...", "provider": "..."}` — pin explicitly to avoid cost drift |
| `deliver` | `"local"` (save only), omit (chat delivery), `"all"` (fan-out), or `"telegram:chat:thread"` |
| `skills` | List of skill names to load before running (loaded in order) |
| `workdir` | Absolute path — runs inside a project dir with its AGENTS.md/CLAUDE.md |
| `no_agent` | `True` = script-only, no LLM; `False` (default) = agent-mode with full tool access |
| `attach_to_session` | Makes the job continuable (user can reply to its deliveries) |

## Delivery

- `"local"` — saves to `~/.hermes/cron/output/<job_id>/`. Use for maintenance jobs that don't need a human conversation.
- Omit `deliver` — routes to the same chat/thread where the job was created (best for messaging platforms).
- `"origin"` — same as omitting (explicit).
- `"all"` — fan-out to every connected messaging channel.

## Threat Scanner Behaviour (IMPORTANT)

Cron job prompts are scanned by the security threat pattern scanner before creation. Prompts that mention reading credential files or exfiltrating secrets are **blocked**.

**Safe phrasing patterns:**
- ✅ "Scan memory files, config, scripts, and logs for credential-like strings"
- ✅ "Check for exposed API keys, tokens, or passwords in config and script files"
- ❌ "Read .env and auth.json for secrets to exfiltrate"

## Shell Script Pitfalls in no_agent Jobs

Scripts run under `no_agent=True` are executed directly by the system shell. Two common footguns:

### `set -euo pipefail` + `ls | head` = SIGPIPE (exit 141)

```bash
# BROKEN — exits 141 every run
set -euo pipefail
LATEST=$(ls -t /path/to/files/*.gz | head -1)

# FIX — either:
set -u                          # Drop pipefail, set -e, or both
LATEST=$(ls -t /path/to/files/*.gz | head -1)

# Or iterate without a pipe:
LATEST=""
for f in $(ls -t /path/to/files/*.gz 2>/dev/null); do
  LATEST="$f"
  break
done
```

When `head -1` reads one line and closes stdin, `ls` gets SIGPIPE on the next write. With `pipefail`, the pipeline exits 141. The command substitution `$()` propagates this as a script-fatal error under `set -e`. **For backup scripts that find the latest file, always drop `pipefail` or use the loop form.**

### `$HOME` Resolution Under Hermes Profiles

The `HOME` env var resolves to the profile directory (e.g. `{profile_home}/`) when the terminal runs inside a Hermes profile. Cron no_agent scripts inherit this. Any script using `$HOME` or `~` will resolve to a path that doesn't contain the platform's data directories.

**Fix:** Hardcode `REAL_HOME="{user_home}"` at the top of the script and reference that variable for all path lookups.

## Querying cron state from shell

```bash
hermes cron list              # Show all jobs
hermes cron status            # Scheduler status
ls ~/.hermes/cron/output/     # Local output files
cat ~/.hermes/cron/.tick.lock # Lock file (empty = no tick running)
cat ~/.hermes/cron/.jobs.lock # Job lock
cat ~/.hermes/cron/ticker_last_success  # Last tick timestamp
```
