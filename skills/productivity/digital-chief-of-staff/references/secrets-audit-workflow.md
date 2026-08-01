# Secrets Audit Workflow

Full procedure for the daily Secrets Audit cron job — scanning Hermes operational files for exposed credentials, vaulting them, and redacting from source files.

## Phase 1 — Scan for Exposed Credentials

Read these files **in order** and inspect for credential-like strings:

1. `~/.hermes/memories/MEMORY.md`
2. `~/.hermes/memories/USER.md`
3. `~/.hermes/config.yaml`
4. Scripts in `~/.hermes/scripts/` (read any non-trivial `.sh` and `.py` files)
5. **All skill files in `~/.hermes/skills/`** — especially reference documents (`.md`) and templates. These commonly include credential examples, truncated API tokens, or full vault JSON dumps inserted as documentation. Run:
   ```bash
   grep -rn 'cfat_\|sbp_\|pk_test_\|pk_live_\|sk-\|ghp_\|gho_\|xox[bpsa]-\|AKIA' ~/.hermes/skills/ --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yaml' --include='*.toml' | grep -v '/.git/'
   ```
6. **State files (secondary scan — informational only):**
   - `~/.hermes/state/rich_sent_index.json` — may contain old message text with credential references
   - Note: these are not actively sourced, so findings go in security notes rather than triggering redaction
7. **Cron output archives (historical scan — informational only):**
   ```bash
   grep -rn 'sbp_\|cfat_\|pk_test_\|pk_live_\|sk- ' ~/.hermes/cron/output/ --include='*.md' 2>/dev/null | grep -v 'REDACTED' | grep -v 'vault:'
   ```
   - Old audit reports may contain full token values in narrative text describing prior findings
   - Findings go in security notes (historical archives, not operational files)
8. Log files (last 50 lines of each):
   - `~/.hermes/logs/gateway.log`
   - `~/.hermes/logs/agent.log`
   - `~/.hermes/logs/errors.log`

### Credential Patterns to Scan For

| Pattern | Example | Type |
|---------|---------|------|
| `sk-` followed by 24+ alphanumeric | `sk-proj-xxxxxxxx` | OpenAI API key |
| `ghp_` / `gho_` / `github_pat_` | `ghp_xxxxxxxxxxxx` | GitHub personal access token |
| `xoxp-` / `xoxb-` | `xoxp-xxxxxxxx` | Slack token |
| `cfat_` | `cfat_[REDACTED - see vault:CLOUDFLARE_API_TOKEN]` | Cloudflare API token |
| `sbp_` | `sbp_[REDACTED - see vault:SUPABASE_PERSONAL_ACCESS_TOKEN]` | Supabase personal access token |
| `pk_test_` / `pk_live_` | `pk_test_[REDACTED - see vault:STRIPE_PUBLISHABLE_KEY]` | Stripe publishable key |
| `sk_test_` / `sk_live_` | `sk_test_xxxx` | Stripe secret key |
| `AKIA` | `<AKIA_EXAMPLE_KEY>` | AWS access key |
| `api_key:` followed by non-empty value | `api_key: abc123` | Generic API key in config |
| `password:` / `secret:` followed by non-empty | `password: hunter2` | Generic secret in config |
| Long alphanumeric 32+ chars in config | `[REDACTED - see vault:CLOUDFLARE_ACCOUNT_ID]` | Account IDs, tokens |

### Files NEVER to Modify

- `~/.hermes/.env` — designated credential store
- `~/.hermes/auth.json` — designated credential store

#### Credential Store Access Behavior

Hermes `read_file` tool **denies access** to `.env` and `auth.json` with a defense-in-depth guard. This is NOT a security boundary — `terminal` (cat, less, etc.) can read both files directly. The guard exists to prevent accidental credential exposure during normal file operations. During audit, use `terminal` when inspection is genuinely needed, not `read_file`.

## Phase 2 — Vault Management (pass password-store)

Credentials are stored in the **`pass` password-store vault** (`{user_home}/.password-store/`), not the old `secrets-vault/vault.json`. The pass vault provides GPG encryption at rest, git versioning, browserpass autofill, and Tailscale-based P2P sync.

### Check the vault
```bash
export PASSWORD_STORE_DIR={user_home}/.password-store
pass ls            # list all stored credentials
pass git log       # view vault change history
```

### Store a new credential
```bash
echo "actual-secret-value" | pass insert --echo category/service/credential-name
```

### Sync after vaulting
```bash
pass git push
```

## Phase 3 — Redact and Store

For each credential found OUTSIDE `.env` or `auth.json`:

1. **Generate a key name** — descriptive path, e.g. `work/cloudflare/api-token`
2. **Add to pass vault** via `pass insert path/to/key`
3. **Redact in source file** — replace the credential string with `[REDACTED - see vault:path/to/key]`

### Redaction Nuances

**Log files have two line formats for the same credential:**
- `gateway.run: inbound message: ... msg='CREDENTIAL_HERE'` — full, no truncation
- `agent.turn_context: conversation turn: ... msg='CREDENTIAL_HERE...'` — same credential, TRUNCATED with `...`

Use `patch()` with `replace_all=True` for the full string, then a separate `patch()` for the truncated variant (with `...` at end).

**Same credential appears in both `gateway.log` and `agent.log`** — the agent.log is an aggregated log that also contains the same gateway.run lines. Scan both files.

**Use `patch` tool** (not sed/terminal) for redaction:
```python
patch(path="~/.hermes/logs/gateway.log",
      old_string="msg='CREDENTIAL: actual_value_here'",
      new_string="msg='CREDENTIAL: [REDACTED - see vault:path/to/key]'")
```

**Use `replace_all=True`** when the same credential string appears in multiple log line formats.

### Verification

After all redactions, verify:

**Step 1 — no raw values remain:**
```bash
grep -n 'raw-credential-value' ~/.hermes/logs/gateway.log ~/.hermes/logs/agent.log
# Should return empty (exit code 1)
```

**Step 2 — all redacted lines visible:**
```bash
grep -n 'REDACTED - see vault' ~/.hermes/logs/gateway.log ~/.hermes/logs/agent.log
# Should show all redacted lines
```

**Step 3 — cross-reference integrity check (both directions):**

```bash
# Find all [REDACTED - see vault:KEY] references outside the vault itself
REFERENCED_KEYS=$(grep -roh 'REDACTED - see vault:[A-Z_]*' ~/.hermes --include='*.md' --include='*.sh' --include='*.py' --include='*.yaml' --include='*.toml' --include='*.json' 2>/dev/null | grep -v 'cron/output/' | grep -v 'secrets-vault/vault.json' | grep -v 'node_modules' | sort -u)
# Parse key names from the references
REF_NAMES=$(echo "$REFERENCED_KEYS" | sed 's/.*vault://')

# Get vault key names from pass
VAULT_KEYS=$(export PASSWORD_STORE_DIR={user_home}/.password-store; pass ls | grep '/' | sed 's/.*infra\///')

# Orphans in vault (key vaulted but no source file references it):
echo "=== Vault entries with no current source file ==="
while IFS= read -r key; do
  found=$(grep -rl "$key" ~/.hermes --include='*.md' --include='*.sh' --include='*.py' --include='*.yaml' --include='*.toml' --include='*.json' 2>/dev/null | grep -v 'secrets-vault/vault.json' | grep -v 'cron/output/' | head -1)
  [ -z "$found" ] && echo "  ⚠ $key — in vault but no source file references it"
done <<< "$VAULT_KEYS"

# Orphans in the wild (reference markers with no vault key):
# (Any reference pointing to a non-existent key will be caught when the next
# audit tries to look up the value. Flag during report phase.)
```

### Interpreting Pattern Search Results

Broad regex scans (e.g., `sk-`, `ghp_`, `AKIA`, JWT) across the full `~/.hermes/` tree will return many matches. Categorize each match:

| Category | Action |
|----------|--------|
| **Designated stores** (`.env`, `auth.json`, `nous_auth.json`) | Ignore — never modify |
| **State snapshots** (`~/.hermes/state-snapshots/*/`) | Ignore — pre-upgrade backup copies of credential stores. Note existence in security notes. |
| **Test fixtures** (`tests/` files with `"moa-virtual-provider"`, `"original-key-entry-1"`, `"«redacted:sk-…»"`) | Ignore — example/placeholder values, not live credentials |
| **Documentation examples** (`"your-api-key"`, `"not-needed"`, `"no-key-required"`) | Ignore — placeholder values in skill docs |
| **Live credentials in operational files** (memories, config, logs, scripts, skill references with actual tokens) | **VAULT AND REDACT** |

The `«redacted:…»` pattern is Hermes' own redaction marker — safe to leave in place. It appears in test fixtures and source code, not in user-facing content.

## Phase 4 — Report Structure

Output a structured report with:

```
# 🛡 Hermes Daily Secrets Audit — Report
**Date:** <timestamp> (cron job <id>)

## Files Scanned
| File | Status | Notes |
|------|--------|-------|
| `memories/` | ✅ Clean | Description |
| `config.yaml` | ✅ Clean | Empty api_key fields |
| `scripts/` | ✅ Clean | No credentials |
| `logs/gateway.log` | ⚠️ Redacted | N instances |
| `logs/agent.log` | ⚠️ Redacted | N instances |

## Credentials Found and Vaulted
| # | Key Name | Source | Value Type |
|---|----------|--------|------------|
| 1 | `work/cloudflare/api-token` | `gateway.log:318`, `agent.log:13245,13251` | Cloudflare API Token |

## Redactions Applied
- `gateway.log` — N lines patched
- `agent.log` — N lines patched (gateway.run + turn_context variants)

## Vault Status
- Store: pass password-store at `{user_home}/.password-store/`
- Entries: N keys
- Git commits: HEAD at <sha>
- Sync: `pass git push` done ✅

## Security Notes
- Any recurring exposure patterns
- Rotation recommendations
- Process improvement suggestions
```

## Common Exposure Sources

### Source A — Telegram DM Logging

Credentials in Hermes logs typically arrive via **Telegram DM messages** from the user. The gateway and agent log every inbound Telegram message verbatim at INFO level. This means:

- Any credential the user sends via Telegram will appear in `gateway.log` and `agent.log`
- The `security.redact_secrets: true` config only redacts on **outbound delivery** — it does not prevent inbound message logging
- This is a **recurring concern** — not a one-time fix

**Mitigation strategies to recommend:**
1. Rotate the exposed keys immediately
2. Instruct user to send credentials via `pass insert` workflow or `.env` instead of Telegram
3. Consider a log redaction pre-processor for known credential patterns before log write
4. Check for rotated log files (`.log.1`, `.log.2`) that may contain unredacted copies
5. Note that session DB (`state.db`) may also contain the raw message text — cannot be scanned programmatically in audit

### Source B — Skill Reference Files

Skill documentation files (`~/.hermes/skills/**/references/*.md`, `SKILL.md`) commonly contain credential values. This happens when:

- A secrets audit or vault workflow reference doc includes real credential values as "examples" in JSON blocks, pattern tables, or sample commands.
- Developer notes or debugging transcripts that captured actual API keys or tokens alongside procedural documentation.
- Template configs or environment variable presets with seeded placeholder values that were never replaced.

**Mitigation:**
1. Scan skills/ as part of every audit (Phase 1 step 5 above)
2. Replace any credential examples with `[REDACTED - see vault:path/to/key]` references
3. Use synthetic example values in documentation (e.g. `sk-proj-xxxxxxxx`, `ghp_xxxxxxxxxxxx`, `cfat_[REDACTED]`) — never real tokens, even truncated
4. **Especially watch for credential values in reference files** — the most common location for credential leaks is a code block that mirrors actual vault contents as "documentation"

### Source C — State Snapshot Directories

`~/.hermes/state-snapshots/<timestamp>-<event>/` is created automatically before upgrades. These directories contain **raw copies** of `.env`, `auth.json`, and `config.yaml` from the moment before the upgrade — live credential material sitting on disk outside the designated stores.

**Status:** These are intentional backup artifacts (not exposures), but they increase the attack surface.

**Mitigation:**
1. Audit: note their existence in the report's security notes section
2. Recommend: clean up old snapshots that are no longer needed
3. Recommend: ensure snapshot directory has `700` (currently `drwxrwxr-x` by default — group-readable)

### Source D — Cron Output Archives (Historical Reports)

`~/.hermes/cron/output/<job-id>/` contains every past run's full report as a `.md` file. These are historical artifacts — not re-executed or sourced — but they **can contain raw credential text** from the run that vaulted them. Example: the report that documents a `sbp_...` Supabase PAT being vaulted may repeat the full token in narrative text for context.

**Status:** Read-only archives of past audits. Real credentials may appear in old reports as part of documenting what was found. Not operational files, not source-of-truth for anything.

**Mitigation:**
1. Audit: grep cron output archives for raw credential patterns — flag any findings in the security notes
2. Not a high-priority redaction target (these are read-once snapshots, not actively sourced files), but note their existence so the user is aware
3. Recommend: future audit reports should use truncated or vault-referenced tokens when describing prior findings in their own output

See also `~/.hermes/state/rich_sent_index.json` — a state file that can contain conversation text with credential references. Scan this as a secondary target during audit; the primary redaction is in the agent.log/gateway.log sources, but the index may retain old references.

## Pass Password-Store Vault Reference

The primary credential vault is now `pass` (password-store), not the old `~/.hermes/secrets-vault/vault.json`.

### Vault location
`{user_home}/.password-store/` (set via `PASSWORD_STORE_DIR` env var — Hermes sessions use a non-standard `$HOME` so the default `~/.password-store` resolves to the wrong path).

### Audit interaction with pass
When the audit finds credentials that need vaulting:

```bash
# Store a found credential
export PASSWORD_STORE_DIR={user_home}/.password-store
echo "actual-secret-value" | pass insert --echo category/service/credential-name

# Verify storage
pass show category/service/credential-name

# Sync to other devices after vaulting
pass git push
```

### Vault verification during audit
```bash
export PASSWORD_STORE_DIR={user_home}/.password-store
pass ls                                # list all vaulted credentials
cd {user_home}/.password-store
git log --oneline -5                   # check vault change history
git remote -v                          # verify sync origin is set
```

### Reference
See `skill_view(name="password-store-vault")` for full setup, browserpass configuration, Tailscale sync workflow, and Hermes integration.
