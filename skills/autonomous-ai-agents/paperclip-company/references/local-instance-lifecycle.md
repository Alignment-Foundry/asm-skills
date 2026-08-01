# Local Paperclip Instance Lifecycle

## Startup

Paperclip runs locally via **npx** — there is no systemd service, no binary on PATH, and no Docker container. The start command is:

```bash
npx paperclipai run
```

This auto-detects the existing config at `~/.paperclip/instances/default/config.json` and uses the embedded PostgreSQL instance.

### Key Details

| Aspect | Value |
|--------|-------|
| Server URL | `http://127.0.0.1:3100` |
| Bind mode | `loopback` (127.0.0.1 only) |
| Deployment mode | `local_trusted` (no auth required for local connections) |
| DB mode | Embedded PostgreSQL, auto-managed by Paperclip |
| DB port | `54329` |
| DB data dir | `~/.paperclip/instances/default/db/` |
| Config file | `~/.paperclip/instances/default/config.json` |
| Runtime node | `@paperclipai/server` (found under `~/.npm/_npx/<hash>/node_modules/`) |
| Log file | `~/.paperclip/instances/default/logs/server.log` |

No systemd unit, no Docker compose — just `npx paperclipai run` which handles both initial setup and subsequent restarts.

## Health Check

The health endpoint responds when the server is up:

```bash
curl -sf -o /dev/null http://127.0.0.1:3100/
# exit code 0 = running, non-zero = down
```

A more detailed check:

```bash
curl -s http://127.0.0.1:3100/api/health
# Returns {"status":"ok",...} when healthy
```

## Watchdog Pattern (Auto-Restart)

Paperclip can die when the host machine restarts (gateway restart, power cycle, etc.). There is no built-in restart mechanism — you need an external watchdog.

### Deterministic Script-Based Watchdog (no_agent=true)

The best approach is a **no_agent=true cron job** running a shell script. This costs zero LLM tokens on every tick — it's a pure `bash + curl` health check that only outputs when action is taken.

**Script logic:**
1. `curl` health check → if up, `exit 0` (silent — nothing to report)
2. If down, kill any stale `node.*@paperclipai/server` process
3. Launch `npx --yes paperclipai run --no-repair &`
4. Poll `curl` up to 30 seconds until the server responds
5. Output a single line on success or failure — cron delivers this only when the script produces stdout
6. On failure, `exit 1` so cron marks the run as failed

**Cron job config:**
- `no_agent=true` — pure script, never invokes the LLM
- `schedule`: every 2-5 minutes (2m is tight enough to catch a gateway restart quickly without being noisy)
- `deliver`: `local` (saved, no notification noise unless the watchdog took action)

See the `scripts/paperclip-watchdog.sh` in this skill directory for the reference implementation.

### Cron Scheduler Restart Behavior

When Hermes restarts (e.g., after a host reboot), the cron scheduler resumes automatically. Cron jobs with past-due schedules fire on restart, so a 2-minute watchdog catches a downed Paperclip within that window of the scheduler coming back online.

## Pitfalls

- **Don't use systemd for Paperclip.** Paperclip's `npx` lifecycle manages its own embedded PostgreSQL. Wrapping it in a systemd service creates dependency ordering problems (PostgreSQL would need to be shut down explicitly on stop).
- **Don't use `--repair` flag on restart.** The `--no-repair` flag avoids the doctor diagnostic step on every restart, making startup ~5s faster.
- **Don't set watchdog interval > 5 minutes.** If Paperclip crashes, you want auto-recovery within minutes, not after a quarter of an hour.
- **Don't run the watchdog via agent-mode cron.** A no_agent script uses zero tokens per tick. An agent-mode cron job would spin up an LLM context, inspect the server, and waste ~20K tokens per 2-minute check just to say "it's fine."