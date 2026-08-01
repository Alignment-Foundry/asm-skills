# Paperclip Backup & Recovery Strategy

> Reference: how Paperclip data is structured locally, what needs backing up, and the recommended approach.

## Data Locations

All Paperclip data lives under `~/.paperclip/instances/default/`:

| Path | Description | Size (typical) | Backup Priority |
|------|-------------|---------------|-----------------|
| `db/` | Embedded PostgreSQL data directory | ~126 MB | Captured by SQL dump |
| `data/storage/` | File attachments (agent outputs, uploads) | ~876 KB | ⭐ Include |
| `data/backups/` | Paperclip auto-generated hourly SQL dumps | ~24 MB each, ~5 GB total (historic) | ⭐ Latest only |
| `projects/` | Project/plan definitions | ~205 MB | ⭐ Include |
| `workspaces/` | Workspace definitions (agent skills, projects) | ~18 MB | ⭐ Include |
| `companies/` | Company configurations + agent instruction bundles | ~328 KB | ⭐ Include |
| `secrets/` | Encrypted secrets vault | ~2 KB | ⭐ Include |
| `config.json` | Server configuration | ~5 KB | ⭐ Include (redact secrets) |
| `.env` | Environment variables for Paperclip | ~164 B | ⭐ Redacted copy |
| `data/run-logs/` | Transient operation logs | varies | ❌ Skip |
| `logs/` | Server logs | ~19 MB | ❌ Skip |

## Paperclip Already Has Auto-Backups

Paperclip generates hourly PostgreSQL dumps automatically at `~/.paperclip/instances/default/data/backups/`:

```
paperclip-YYYYMMDD-HHMMSS.sql.gz
```

- **Format:** `pg_dump` SQL gzipped
- **Frequency:** Every hour at :44 past
- **Size:** ~24 MB compressed each (~25 MB compressed)
- **Retention:** Accumulates indefinitely (no auto-prune — 164+ backups = 4.9 GB)

These cover the database (agents, issues, comments, budgets, settings). They do NOT cover projects, workspaces, secrets, storage, or config files.

## External GitHub Backup Pattern

For a complete off-machine backup, use a `no_agent=true` cron script that:

1. **Clones the target repo** (private, on GitHub)
2. **Copies the latest DB dump** from `data/backups/`
3. **Copies non-DB config dirs:** `companies/`, `projects/`, `workspaces/`, `secrets/`, `data/storage/`
4. **Redacts secrets** from `config.json` and `.env`
5. **Commits and pushes** any changes

### Script deployment

Scripts must be placed in the **active profile's** scripts directory, not the default:

| Profile | Scripts Dir |
|---------|-------------|
| Default | `~/.hermes/scripts/` |
| Alpha | `~/{profile}/scripts/` |

Cron jobs resolve `script` paths relative to the profile's scripts dir. A script at `~/.hermes/scripts/foo.sh` will not be found by an alpha-profile cron.

### .gitignore

Always include `node_modules/` in the backup repo's `.gitignore`. Workspace projects can contain npm dependencies that bloat the backup needlessly.

### Paperclip DB backup location

Internal backups live at `~/.paperclip/instances/default/data/backups/`. To get the latest:

```bash
LATEST=$(ls -t ~/.paperclip/instances/default/data/backups/paperclip-*.sql.gz 2>/dev/null | head -1)
```

## Pitfalls

- **`HOME` variable may point to profile directory** in cron/terminal contexts. Always hardcode `{user_home}` or use `REAL_HOME="{user_home}"` in scripts rather than `$HOME`.
- **Avoid `set -euo pipefail` in backup scripts.** The `ls -t | head -1` pattern can produce SIGPIPE (exit 141). Use a `for f in $(ls ...); do ...; break; done` loop instead.
- **Node.js workspaces can contain `node_modules/`.** Strip them with `find workspaces -depth -type d -name node_modules -exec rm -rf {} +` after copy.
- **API keys in `config.json` need redaction.** Common keys: `token`, `apiKey`, `secret`, `password`.
