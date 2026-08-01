# Hermes Profile Tilde-Expansion Workaround

## Problem

Under Hermes profiles, `$HOME` is set to the profile directory (e.g. `~/{profile_home}/`), **not** the actual user home (`{user_home}`). Any CLI tool that resolves `~` at runtime will look in the wrong place for config files, venvs, and credentials.

**Symptoms:** Config-not-found errors from CLIs that auto-discover config via `~/.config/`, venv activation failures via `source ~/.venv/`, and random `$XDG_*` resolution issues.

## Fix — Always Use Absolute Paths

In `terminal()` calls under a Hermes profile, NEVER use `~` or `$HOME`-relative paths. Use fully-resolved `{user_home}/...` paths.

### Pattern

```bash
# ❌ Wrong — tilde resolves to profile dir
source ~/{email_venv}/bin/activate
himalaya envelope list

# ✅ Right — absolute path
source {user_home}/{email_venv}/bin/activate
himalaya --config {user_home}/.config/himalaya/config.toml envelope list
```

### Affected patterns

| Pattern | Replacement |
|---------|-------------|
| `source ~/{email_venv}/bin/activate` | `source {user_home}/{email_venv}/bin/activate` |
| `himalaya ...` (without `--config`) | `himalaya --config {user_home}/.config/himalaya/config.toml ...` |
| `cat ~/.config/foo` | `cat {user_home}/.config/foo` |
| Any `~/.hermes/` ref in shell commands | `{hermes_home}/` |
| Any `~/.local/` or `~/.cache/` ref | `{user_home}/.local/` or `{user_home}/.cache/` |

This applies to ALL CLI tools when running under a Hermes profile — Rust/Go CLIs that resolve `$HOME` at runtime are the most common offenders. Python tools via a sourced venv usually inherit the correct `$HOME`, but external binaries (himalaya, flyctl, gh) do their own resolution.
