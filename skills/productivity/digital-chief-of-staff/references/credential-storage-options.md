# Credential Storage Options for Hermes & Agent Ecosystems

Reference for evaluating credential/secret management approaches compatible with Hermes, multi-device sync, and agent access.

## Decision Framework

| Criterion | Weight | Ask yourself |
|-----------|--------|-------------|
| **Infra footprint** | High | Is zero-infrastructure required, or is a server/VPS acceptable? |
| **Agent safety** | High | Can secrets be injected without agents seeing raw values? |
| **Encryption at rest** | Required | Are creds encrypted when not in use? |
| **Multi-device sync** | Medium | How do creds flow between laptop, server, agents? |
| **Per-credential access control** | Low→Med | Do different agents need different subsets of creds? |
| **Audit trail** | Low→Med | Do you need to know who accessed what when? |

## Option Landscape

### Family A — File-Level Encryption (Zero Infra)

Encrypt credential files with age/GPG, store in git. Simplest model.

| Tool | Encryption | Sharing | Agent compat | Notes |
|------|-----------|---------|-------------|-------|
| **age** (standalone) | age (X25519/Ed25519) | Multi-recipient, manual | `age -d -i key.txt vault.json.age` | Simplest building block. No access control. |
| **SOPS + age** | age per-value in JSON/YAML/ENV | Multi-recipient in `.sops.yaml` | `sops decrypt vault.enc.json` | Mozilla-audited, mature (15k+ stars). Per-file rules. |
| **agebox** | age full-file | Git only | `agebox decrypt` | Lightest — just age wrapper. No access control. |
| **git-crypt** | Transparent git filter | GPG per-committer | `git-crypt unlock` | Transparent — files decrypt on checkout. GPG-only. |
| **git-secret** | GPG per-file | GPG per-recipient | `git-secret reveal` | GPG complexity. No env injection. |

### Family B — Dedicated Secret Manager CLIs (Minimal Infra)

Purpose-built CLI tools with age-based encryption and git or API sync.

| Tool | Encryption | Sharing | Agent compat | Highlights |
|------|-----------|---------|-------------|-----------|
| **Cottage** | age (Rust) | Git + `.cottage/recipients` | `ctg env -- ./agent.py` (env injection, no disk write) | Access control per secret, redacted previews, CI verification, upstream plugin system (1Password, Vault, etc.), Cottage Sync for cross-device. New but active (v0.6.5, June 2026). |
| **Phase** | E2EE client-side | Server API (self-hostable) | `phase run -- ./agent.py` + dedicated AI skill install (`phase ai enable`) | **Three secret types** with AI visibility rules: `config` (always visible), `secret` (configurable), `sealed` (never visible to agents). Agent guardrails block `printenv`/`export` inside `phase run`. Offline cache mode. Requires Docker Compose (Postgres + Redis) if self-hosted. |

### Family C — P2P / Decentralized

No central server — peers sync directly.

| Approach | How it works | Best for |
|----------|-------------|----------|
| **PearPass** (Holepunch/Tether) | Desktop+Mobile P2P password manager built on Pear Runtime (Hypercore/Hyperdrive/Hyperswarm). E2EE, P2P sync with no cloud. Open source. Independently audited. | True zero-infra P2P. ❌ No CLI/API — GUI only, so Hermes can't fetch secrets programmatically. Good for personal credentials only. |
| **Syncthing + age-encrypted files** | Syncthing P2P syncs `.json.age` files between devices. Each device has its own age key. Remote/untrusted devices store encrypted blobs only. | Zero server infra, P2P-native, battle-tested sync (65k+ stars). No access control per credential — it's all-or-nothing per folder. |
| **Tailscale + age vault** | All devices on a tailnet. One device serves an age-encrypted vault file over the tailnet (no public exposure). Other devices curl and decrypt locally. Tailscale ACLs control which devices can reach the server. | Zero infra beyond Tailscale. WireGuard transport encryption. Tailscale ACLs act as firewall. |
| **Tailscale + lightweight cred server** | A minimal HTTP key-value server running on the tailnet (e.g. 50-line Python script). Agents/Devices fetch creds by key over the tailnet. Tailscale ACLs restrict access. | Customizable, programmatic agent access. You build the server. No encryption at rest (relies on Tailscale transport). |
| **Tailscale + Phase (self-hosted)** | Run Phase's Docker Compose stack behind Tailscale — only accessible from the tailnet. `phase run` injects secrets as env vars. | Full-featured (E2EE, sealed secrets, RBAC). Needs a VPS or device running Docker. |
| **Cottage Sync** | Dedicated cross-device sync overlay for Cottage secrets. | If already using Cottage — layers device sync on top of its git+age model. |

### Family D — Self-Hosted Vault Server

Run a server (lightweight VPS OK). Best for multi-user teams, audit trails, web UI.

| Tool | Stack | Sharing | Agent compat | Footprint |
|------|-------|---------|-------------|-----------|
| **Vaultwarden** | Rust, SQLite | Bitwarden orgs/collections | `bw get password <item>` | Single binary + SQLite. ~50 MB RAM. |
| **Infisical** | Postgres + Redis + Node | Service tokens, RBAC, environments | `infisical run -- ./agent.py` | Docker Compose. ~200 MB RAM. Web dashboard. |
| **HashiCorp Vault** | Go, storage backend | Policies, tokens, approles | `vault read secret/creds` | Heavy — needs storage backend (Consul, Raft, etc.). Often overkill for single-user. |

## Agent Safety Patterns

When an AI agent has access to credentials, you need guardrails:

| Pattern | How it works | Tools that support it |
|---------|-------------|----------------------|
| **Sealed/write-only** | Agent can write/rotate secrets but never read them back | Phase (sealed type), AgentSecrets |
| **Env injection** | Secrets injected as env vars before the agent process starts — agent never reads the vault file | `phase run`, `ctg env`, `infisical run`, `doppler run` |
| **Just-in-time** | Agent calls an API to get a short-lived credential that expires | Vault dynamic secrets, Infisical dynamic secrets, Phase dynamic secrets |
| **One-shot decryption** | Decrypt file to temp location, agent runs, file deleted after | `ctg run` / `ctgx` |
| **Redacted output** | Secret values masked in agent output/logs | Phase (AI guardrails block `printenv`), Hermes (`security.redact_secrets`) |

## Existing Infrastructure (This Hermes Instance)

| Component | Location | Purpose |
|-----------|----------|---------|
| Daily Secrets Audit | Cron job `1508b836b34b` at 2AM | Scans memories, config, scripts, logs for exposed credentials; vaults to JSON; redacts source files |
| Local vault (legacy) | `~/.hermes/secrets-vault/vault.json` (chmod 600) | Plain JSON with key-value pairs + `__notes` metadata |
| **pass (password-store)** | `~/.password-store/` (GPG-encrypted, git-backed) | Upgraded local vault — GPG-encrypted per-credential files, browser autofill via browserpass, git-over-Tailscale sync |
| Designated stores | `~/.hermes/.env`, `~/.hermes/auth.json` | Never modified by audit — these are the canonical Hermes credential locations |
| Exclusion from backup | `secrets-vault/` dir excluded from Hermes backup scripts | Security — creds should not live in git |

**Current state:** detection + redaction pipeline exists. Storage is plain JSON with filesystem-only protection. No sharing, no encryption at rest beyond chmod.

## Recommendations by Use Case

| If you need... | Start here |
|----------------|-----------|
| **Simplest upgrade from vault.json** | `age`-encrypt the existing vault.json, add pubkeys for each device. No infra, no new tools beyond `age`. |
| **Zero infra + per-cred access + env injection** | **Cottage** — `ctg init` in your creds directory, `ctg env -- ./deploy.sh` for agents. Git-backed distribution. |
| **Agent-first with sealed secrets** | **Phase** — `phase ai enable` installs a skill; sealed secrets never visible to agents. Requires a Docker Compose host. |
| **P2P multi-device sync** | **Syncthing** folders for age-encrypted files. Devices sync directly — no server, no git push. |
| **Full team platform** | **Infisical** — RBAC, environments, web dashboard, Kubernetes operator. |

## Installed Tools (as of July 2026)

| Tool | Status | Version |
|------|--------|---------|
| `pass` | ✅ installed | 1.7.4 |
| `webext-browserpass` | ✅ installed | via apt (Firefox + Chrome native hosts) |
| `tailscale` / `tailscaled` | ✅ installed | 1.80.3 |
| `gpg` | ✅ installed | 2.4.4 |
| `age` | ❌ not installed | — |
| `sops` | ❌ not installed | — |
| `ctg` (cottage) | ❌ not installed | — |
| `phase` | ❌ not installed | — |
| `syncthing` | ❌ not installed | — |
| `git-crypt` | ❌ not installed | — |
| `git-secret` | ❌ not installed | — |
