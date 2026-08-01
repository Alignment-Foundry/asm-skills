# ASM Skills

A portable, agent-agnostic repository of reusable skills for AI coding agents.

See [SKILL.md](SKILL.md) for the canonical project specification.

## Quick Links

- **Validate all skills:** `python3 scripts/validate-skills.py`
- **Install a skill for Hermes:** `bash scripts/sync-skill.sh productivity/code-review`
- **Create a new skill:** Copy `skills/_template` to `skills/<category>/<name>/`
- **GitHub:** https://github.com/Alignment-Foundry/asm-skills
- **License:** MIT

## Publishing & Review

This repo is a **curated, genericized publication subset** of a live skill store —
NOT a mirror. Local skills stay specific to their owner's use; published copies
are generic derivatives. Nothing new publishes without review.

**The publish gate flow:**

1. **Port** — `scripts/port-skills.py` copies approved skills from the local store.
   Skills not marked `approved` in the holdlist are skipped; new or updated skills
   are auto-added as `pending-review` (nothing new publishes without approval).
2. **Review** — `.publish-holdlist.md` (repo root, **private** — gitignored, never
   committed) holds review state: `| skill | status | reason | date | notes |`,
   status ∈ `pending-review` (default), `approved`, `blocked`.
3. **Audit** — run all three scanners; all must exit 0:
   ```bash
   python3 scripts/audit-credentials.py   # credential patterns
   python3 scripts/audit-pii.py           # emails, phones, IPs
   python3 scripts/audit-generic.py       # identifying topical markers
   ```
4. **Push** — only after audits pass. CI re-runs the scanners on every push/PR
   (genericness in CI uses placeholder markers; real enforcement is local).

**Private files — set up your local gate:**

```bash
# 1. Copy the example marker config and fill in YOUR identifying markers
#    (names, projects, orgs, jargon, paths). Keep it private — never commit.
cp .audit-generic-markers.example.json .audit-generic-markers.json
# 2. .publish-holdlist.md is created/updated by port-skills.py; review items
#    surface in the daily digest. Approve/block entries by editing the table.
```

`.audit-generic-markers.example.json` is committed (schema + placeholder markers
only) so fresh clones and CI know the format without exposing anything.

## Scripts

All scripts run from the repo root: `python3 scripts/<name>.py` / `bash scripts/<name>.sh`.

### validate-skills.py

Validates every `skills/**/SKILL.md`: YAML frontmatter parses, `name` and
`description` present (description ≤ 1024 chars), non-empty body, file ≤ 100 KB.

- Usage: `python3 scripts/validate-skills.py`
- Exit: 0 = all skills valid, 1 = validation errors

### port-skills.py

Ports user-created skills from a Hermes local store into `skills/` (SKILL.md +
references/scripts/templates/assets copied as-is). Runs the **holdlist gate**:

- Skills with holdlist status other than `approved` are skipped and reported as
  "on hold — pending Alex review".
- Skills missing from the holdlist (new) are auto-added as `pending-review` and
  skipped — nothing new publishes without approval.
- An `approved` skill whose content changed since the last port is flipped back
  to `pending-review` and skipped until re-approved.
- After porting, prints a reminder to run all three audits before push.

Configuration (the repo is public, so no local paths are hardcoded):

```bash
HERMES_PROFILE_DIR=/home/you/.hermes/profiles/alpha \
HERMES_PROJECTS_DIR=/home/you/projects \
python3 scripts/port-skills.py
# Optional: port a subset
PORT_SKILLS="software-development/efficient-operation,github/github-org-ops" \
  python3 scripts/port-skills.py
```

The holdlist lives at `.publish-holdlist.md` (gitignored). If absent, the script
treats every skill as new and flags them all `pending-review`.

### sync-skill.sh

Symlinks (or copies with `--copy`) a skill from this repo into a Hermes local
skills dir — the reverse direction of port-skills.py.

- Usage: `bash scripts/sync-skill.sh <category>/<skill-name> [--copy]`
- Target dir: `${HERMES_SKILLS_DIR:-$HOME/<profile>/skills}` (override the env var)

### audit-credentials.py

Scans the repo for credential patterns (API keys `sk-`, `ghp_`, `github_pat_`,
`AKIA`; Slack/Stripe/Telegram tokens; PEM private keys; JWT-like tokens; DB auth
URLs). Scanner files and placeholder/example patterns are auto-excluded.

- Usage: `python3 scripts/audit-credentials.py`
- Exit: 0 = clean, 1+ = findings to review/redact

### audit-pii.py

Scans the repo for PII: email addresses, phone numbers, IP addresses. Safe
domains (`example.com`, etc.), private IP ranges, and localhost are filtered.

- Usage: `python3 scripts/audit-pii.py`
- Exit: 0 = clean, 1+ = findings to review/redact

### audit-generic.py

Scans the repo for identifying topical markers (proper nouns, project names,
orgs, jargon, path patterns) — the genericness gate. Reads the marker list from
`.audit-generic-markers.json` (repo root, **private**, gitignored):

```json
{
  "markers": {"proper_nouns": [], "projects": [], "orgs": [], "jargon": [], "paths": []},
  "exclude_files": []
}
```

- Markers match case-insensitively as substrings of a line.
- `exclude_files` lists repo-root-relative files that legitimately carry a
  marker (e.g. root identity docs, meta-docs that name the repo/org).
- A marker matching a skill's own directory name is allowed inside that skill's
  directory (a skill names itself; the marker catches that name leaking into
  other skills).
- Gitignored files are skipped — only publishable content is scanned.

Behavior:

- If `.audit-generic-markers.json` exists → scans with your private markers
  (local enforcement mode).
- If only the committed `.audit-generic-markers.example.json` exists (fresh
  clone / CI) → scans with placeholder markers and notes it (CI-safe).
- If neither exists → exits 2 with instructions to copy the example.

- Usage: `python3 scripts/audit-generic.py`
- Exit: 0 = clean, 1 = marker hits (redact or exclude before push), 2 = config error

Real genericness enforcement is the **local pre-push gate**: CI only sees the
placeholder example markers by design.
