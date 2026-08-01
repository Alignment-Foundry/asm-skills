---
name: "nous-credits-check"
title: "Nous Portal Credits Check"
version: "2.0"
description: "Check and report Nous Portal credits balance — with Telegram-friendly Markdown table output — bundled as a self-contained skill"
triggers:
  - "check nous credits"
  - "nous portal balance"
  - "credit report"
  - "subscription status"
related_skills:
  - token-usage-report
---

# Nous Portal Credits Check

A CLI tool and cron job that queries `https://portal.nousresearch.com/api/oauth/account` via the existing Hermes OAuth session and reports current credit/subscription status.

## Script (Bundled)

The Python script lives inside the skill directory as `scripts/nous-credits.py`. Run it directly:

```bash
# Via the skill's bundled wrapper
~/{profile}/scripts/nous-credits.sh [flags]
```

Or reference the bundled script directly:

```bash
python3 {profile}/skills/monitoring/nous-credits-check/scripts/nous-credits.py [flags]
```

## Output Modes

| Flag | Purpose |
|------|---------|
| *(none)* | Unicode box-drawing table (terminal) |
| `--json` | Structured JSON for programmatic use |
| `--quiet` / `-q` | One-line summary |
| `--markdown` / `--tg` | **Markdown pipe table (Telegram-friendly)** |
| `--force-fresh` | Bypass JWT cache, hit live API |
| `--check-threshold 10` | Exit code 2 if credits < $10 |

## Telegram Gateway Convention

**When the delivery channel is Telegram, ALWAYS use `--markdown` output mode.** The Unicode box-drawing characters (`┌─┐│└┘├┤`) in the default human report do not render properly on Telegram. The `--markdown` flag outputs a clean pipe table that Telegram renders natively:

```
| Field                   | Value                                |
|-------------------------|--------------------------------------|
| Source                  | Portal API (fresh)                   |
| Plan                    | Plus                                 |
| Tier                    | 2                                    |
| Monthly                 | $20.00                               |
```

### Cron Job Behavior

The cron job `nous-credits-check` runs every 7 days and is **agent-driven** (not `no_agent`). The agent loads this skill and follows these rules:

1. If delivering to **Telegram**: use `nous-credits --markdown` for the full table, or `nous-credits --quiet` for a compact one-liner
2. If delivering to **terminal/CLI**: use `nous-credits` (default box-drawing) or `nous-credits --quiet`
3. If credits are below **$5.00**: append a **bold alert** in the message
4. Always include the top-up URL when credits are low: `https://portal.nousresearch.com/billing`

## Quick Run

```bash
# Full Markdown table (Telegram)
~/{profile}/scripts/nous-credits.sh --markdown

# One-line for status bar
~/{profile}/scripts/nous-credits.sh --quiet

# Fresh from API
~/{profile}/scripts/nous-credits.sh --force-fresh --markdown
```
