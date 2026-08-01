---
name: password-store-vault
description: "Set up and manage a local GPG-encrypted credential vault using pass (password-store) with browserpass autofill, Tailscale-based P2P sync across devices, and Hermes integration for credential injection."
version: 1.1.0
author: Alpha
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [credentials, secrets, pass, gpg, browserpass, tailscale, security, vault]
    category: security
---

# Password-Store Vault

Use `pass` (password-store) as a local, GPG-encrypted, git-versioned credential vault with browser autofill via browserpass and P2P sync across devices via Tailscale.

## Architecture

```
~/.password-store/
├── .git/                          ← Git repo for sync (pushed to a bare repo)
├── .gpg-id                        ← Your GPG key ID
├── work/                          ← Service-category folders
│   ├── cloudflare/api-token.gpg
│   ├── stripe/publishable-key.gpg
│   └── supabase/database-password.gpg
├── infra/
└── personal/
```

## Installation

```bash
sudo apt-get install pass pass-extension-otp webext-browserpass
```

### Generate GPG key (if you don't have one)

```bash
cat > /tmp/gpg-batch << 'EOF'
Key-Type: eddsa
Key-Curve: ed25519
Subkey-Type: ecdh
Subkey-Curve: cv25519
Name-Real: Your Name
Name-Email: you@example.com
Expire-Date: 0
%commit
EOF

gpg --batch --gen-key /tmp/gpg-batch
gpg --list-secret-keys --keyid-format=long
```

### Initialize the store

```bash
# CRITICAL: if $HOME points to a non-standard path (e.g. Hermes profile), 
# set PASSWORD_STORE_DIR explicitly, otherwise pass will create the store
# under the wrong $HOME path.
export PASSWORD_STORE_DIR="$HOME/.password-store"

# Initialize with your GPG key ID
pass init <GPG_KEY_ID>

# Verify
pass ls
```

### Set up git

```bash
cd "$PASSWORD_STORE_DIR"
git init
git config user.name "Your Name"
git config user.email "you@example.com"
```

## Editor

`pass edit` and `pass insert` use `$EDITOR`. Set it in `~/.bashrc`:

```bash
export EDITOR="code --wait"       # VS Code
# or
export EDITOR="nano"              # Nano
# or
export EDITOR="vim"               # Vim
```

Add to `~/.bashrc` alongside the `PASSWORD_STORE_DIR` export.

## Daily Usage

| Task | Command |
|------|---------|
| Store a secret | `pass insert path/to/key` |
| View a secret | `pass show path/to/key` |
| Copy to clipboard (45s) | `pass -c path/to/key` |
| Generate random pw | `pass generate path/to/key 32` |
| Edit a secret | `pass edit path/to/key` |
| List all | `pass ls` |
| Search across entries | `pass grep "search-term"` |
| Push to sync origin | `pass git push` |
| Pull updates | `pass git pull` |

Organize by service category using path prefixes:

```bash
pass insert infra/cloudflare-api-token
pass insert work/stripe/live-secret-key
pass insert personal/github-token
pass insert services/posthog/project-api-key
```

## Browserpass Integration

### Native host (already installed)

The `webext-browserpass` package installs the native messaging host:

- **Firefox:** `/usr/lib/mozilla/native-messaging-hosts/com.github.browserpass.native.json`
- **Chrome/Chromium:** Must copy the native messaging host file to `/etc/opt/chrome/native-messaging-hosts/` (or symlink):
  ```bash
  sudo mkdir -p /etc/opt/chrome/native-messaging-hosts
  sudo cp /usr/lib/mozilla/native-messaging-hosts/com.github.browserpass.native.json \
    /etc/opt/chrome/native-messaging-hosts/
  ```
  Then update the `allowed_extensions` to `allowed_origins` for Chrome format:
  ```json
  {
    "name": "com.github.browserpass.native",
    "path": "/usr/lib/browserpass/browserpass-native",
    "type": "stdio",
    "allowed_origins": [
      "chrome-extension://jkdmgdpkkggjhjckkpdgccokejgmdoeg/"
    ]
  }
  ```

### Browser extension

- **Chrome/Edge:** Install [browserpass from Chrome Web Store](https://chromewebstore.google.com/detail/browserpass/jkdmgdpkkggjhjckkpdgccokejgmdoeg)
- **Firefox:** Install [browserpass from AMO](https://addons.mozilla.org/firefox/addon/browserpass/)

Name entries by domain for autofill to work automatically:
```bash
pass insert cloudflare.com/login
pass insert github.com/personal
```

## Tailscale P2P Sync

### Architecture

```
Device A (origin)           Device B              Device C
  bare git repo  ──tailnet──►  git clone   ──tailnet──►  git clone
  pass git push              pass git pull          pass git pull
```

### Origin device setup

```bash
# Create a bare repo to act as the sync origin
mkdir -p ~/{pass-bare-repo}
cd ~/{pass-bare-repo}
git init --bare

# Link your password store to it
cd ~/.password-store
git remote add origin {user_home}/{pass-bare-repo}
git push -u origin main
```

Once Tailscale is authenticated (`tailscale up --operator=$USER`), get your tailnet IP:

```bash
tailscale ip -4
# → 100.x.x.x
```

Then update the remote to use Tailscale SSH:

```bash
cd ~/.password-store
git remote set-url origin {user}@100.x.x.x:{user_home}/{pass-bare-repo}
```

### New device setup

```bash
# Install pass + browserpass
sudo apt-get install pass webext-browserpass

# Import the GPG public key from the origin device
gpg --import pubkey.asc
gpg --edit-key <KEY_ID>
# Type: trust → 5 → quit

# Clone the password store over Tailscale SSH
git clone {user}@100.x.x.x:{user_home}/{pass-bare-repo} ~/.password-store

# Set PASSWORD_STORE_DIR for future use
echo 'export PASSWORD_STORE_DIR="$HOME/.password-store"' >> ~/.bashrc

# Verify
pass ls
```

### Day-to-day sync

```bash
pass git push   # after adding/editing credentials
pass git pull   # before reading on another device
```

## Diagnostics

When `pass show` fails, the error message tells you exactly where the problem is:

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `No secret key` | GPG homedir doesn't have your private key | Copy the right `.gnupg/` (see `references/troubleshooting.md`) |
| `Timeout` | pinentry can't prompt (GNOME pinentry in headless terminal) | Configure pinentry-curses in `gpg-agent.conf` |
| `No passphrase given` | Key recognized but passphrase isn't cached | Run `pass show` once to trigger the pinentry prompt |
| `Decryption failed: Unknown system error` | Invalid input or wrong homedir | Verify the `.gpg` file and keyring match |

For step-by-step diagnosis of each error, see `references/troubleshooting.md`.

## Hermes Integration

### Env var injection

Source credentials before launching Hermes:

```bash
#!/bin/bash
# ~/bin/hermes-with-creds
export PASSWORD_STORE_DIR="$HOME/.password-store"
export OPENROUTER_API_KEY=$(pass show work/cloudflare/api-token)
export CLOUDFLARE_API_TOKEN=$(pass show work/cloudflare/api-token)
export SUPABASE_PAT=$(pass show work/supabase/personal-access-token)

exec hermes "$@"
```

```bash
chmod +x ~/bin/hermes-with-creds
hermes-with-creds
```

### One-off credential lookup from a script or terminal

```bash
export PASSWORD_STORE_DIR="$HOME/.password-store"
pass show example-app/production/api-key
```

## Secure Credential Handling

### When you find credentials in plaintext files

1. **Store in pass first** — insert each credential into the vault
2. **Shred the original** — use `shred -u` not `rm` (shred overwrites before unlinking)
3. **Replace with a safe index** — a text file listing `pass show` paths with no actual values
4. **Clean bash history** — `cat /dev/null > ~/.bash_history && history -c`

```bash
# Safe replacement workflow
shred -u /path/to/plaintext/credentials.txt
echo "See pass vault" > /path/to/replacement-index.txt
```

### SUDO_PASSWORD handling

If you added a `SUDO_PASSWORD` to `.env` for Tailscale/package installation:

1. Remove it immediately after setup: `grep -v 'SUDO_PASSWORD' .env > /tmp/env_clean && cp /tmp/env_clean .env`
2. Clear sudo credential cache: `sudo -k`
3. Clear bash history: `cat /dev/null > ~/.bash_history && history -c`
4. Delete any temp files that contain it
5. Do NOT write it to memories or skill docs

## Pitfalls

- **`$HOME` mismatch in Hermes profiles:** Hermes sessions set `HOME` to the profile's home directory (`/home/user/.hermes/profiles/<name>/home/`), not the real home. `pass` uses `$HOME/.password-store` by default, so it creates the store inside the Hermes profile directory. **Fix:** Always set `PASSWORD_STORE_DIR` to the real password-store path before any `pass` command, and export it in `.bashrc`.
- **GPG keyring also splits on `$HOME`:** The same Hermes `$HOME` issue affects GPG — keys created inside Hermes sessions live in the profile's `.gnupg/`, not the real `~/.gnupg/`. When `pass` works in Hermes but fails with "No secret key" in a normal terminal, the fix is to copy the Hermes profile's GPG keyring to the real home (see `references/troubleshooting.md`). Includes both `pubring.kbx` and `private-keys-v1.d/` — the `.key` files inside `private-keys-v1.d/` hold the actual private key material.
- **pinentry-gnome3 times out in headless terminals:** The default pinentry on Ubuntu is `pinentry-gnome3`, which requires X11. In SSH, TUI, or any headless context, GPG decrypt fails with "Timeout". **Fix:** Create `~/.gnupg/gpg-agent.conf` with `pinentry-program /usr/bin/pinentry-curses`, then reload the agent.
- **Passphrase caching:** Without `gpg-agent.conf`, the default cache TTL is 600s (10 minutes). Set `default-cache-ttl 3600` and `max-cache-ttl 86400` in `gpg-agent.conf` for 1h cache / 24h max. Run `pass show some/entry` once per session to prime the cache; subsequent `-c` commands skip the prompt.
- **Tailscale `--port=` empty string:** The default systemd service file uses `--port=${PORT}`. If `PORT` is empty (as in the default env file), this becomes `--port=` which is invalid. **Fix:** Hardcode `--port=0` in the service file instead of using the variable.
- **Tailscale auth:** Run `tailscale up --operator=$USER` first, then `tailscale up` as the regular user to get the auth URL.
- **`pass insert` vs `pass insert --echo`:** Without `--echo`/`--multiline`, `pass` prompts for the password hidden (no echo). With `--echo`, it shows what you type — useful when piping, but avoid it for interactive use on shared screens.
- **shred vs rm:** `shred -u file` overwrites the file 3x before deleting. `rm` only removes the directory entry. Use `shred` for anything that contained credentials.
