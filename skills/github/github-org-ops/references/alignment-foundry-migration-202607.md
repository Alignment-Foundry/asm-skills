# Session Reference: Alignment-Foundry Migration (Jul 2026)

This reference captures the specific repos migrated and PAT used in the Jul 2026 session.

## Migrated Repos

| Project | Source | Target | Visibility |
|---------|--------|--------|-----------|
| {private-repo-website-label} | `{dev_account}/{private-repo-website-src}` | `{org}/{private-repo-website}` | Private |
| {private-repo-convo-label} | `{dev_account}/{private-repo-convo-src}` | `{org}/{private-repo-convo}` | Private |
| {private-repo-dox} | `{dev_account}/{private-repo-dox-src}` | `{org}/{private-repo-dox}` | Private |
| dox-scaffold | `{dev_account}/dox-scaffold` | `Alignment-Foundry/dox-scaffold` | Public (was already there) |

## Dox-scaffold v0.5.0 Release

Removed Hermes-specific notation (`--agent hermes`, `.hermes.md`, `make_hermes_md()`, `skills/dox-scaffold/`). Clean two-mode agent model: `--agent default` → AGENTS.md, `--agent claude` → CLAUDE.md at every level.

11 files changed, 25 insertions, 278 deletions.

## PAT Notes

The fine-grained PAT (created under `{dev_account}` account,
granted repo creation permissions for `Alignment-Foundry` org) was:
- Stored via git credential helper for future pushes

## Auth Error (Default Profile)

The default Hermes profile's Nous OAuth had an `invalid_grant` error (refresh token invalidated when alpha profile re-authed). Fixed by importing shared credentials via `hermes auth add nous --profile default`.
