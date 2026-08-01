# pass + browserpass + Tailscale — Local Credential Vault

A zero-infrastructure credential management architecture combining the Unix `pass` (password-store) CLI with browser autofill via `browserpass`, synced across devices over a Tailscale mesh VPN. Each credential is its own GPG-encrypted file — git-backed, CLI-native, zero servers.

## Architecture

```
~/.password-store/                      ← GPG-encrypted files on disk
├── .git/                               ← git repo (local + tailnet bare remote)
├── infra/
│   ├── cloudflare-api-token.gpg
│   └── supabase-pat.gpg
└── hermes/
    └── openrouter-key.gpg

Distribution:
  Device A ──── git push/pull ──── tailnet origin ──── git push/pull ──── Device B
  (alpha)      (over Tailscale SSH)  (bare repo on one host)                (laptop)

Browser autofill:
  pass CLI → GPG decrypt → browserpass native host → browserpass extension → browser
```

## Components

| Component | Purpose | Ubuntu package |
|-----------|---------|----------------|
| `pass` | CLI password store, GPG-encrypted files | `apt install pass` |
| `browserpass` | Browser autofill native host | `apt install webext-browserpass` |
| browserpass extension | Chrome/Firefox add-on | Chrome Web Store / Firefox Add-ons |
| Tailscale | Mesh VPN for P2P device connectivity | Static binary from pkgs.tailscale.com |
| GPG | Encryption per credential file | Pre-installed on Ubuntu |

## Setup (Verified, This Machine)

### 1. Install Tailscale

The `curl ... install.sh | sh` pipe **does not work** in automated contexts (sudo password piped via stdin gets blocked by Hermes security). Use the static binary tarball instead:

```bash
# Download the static tarball
curl -fsSL -o /tmp/tailscale.tgz \
  "https://pkgs.tailscale.com/stable/tailscale_1.80.3_amd64.tgz"
cd /tmp && tar xzf tailscale.tgz

# Install binaries
sudo cp tailscale_1.80.3_amd64/tailscale /usr/local/bin/
sudo cp tailscale_1.80.3_amd64/tailscaled /usr/local/bin/
sudo cp tailscale_1.80.3_amd64/systemd/tailscaled.service /etc/systemd/system/
```

**CRITICAL — Fix the systemd service file.** The service template uses `--port=${PORT}` which produces `--port=` (empty string) when `$PORT` is unset, causing exit status 2:

```bash
sudo sed -i 's/--port=${PORT}/--port=0/' /etc/systemd/system/tailscaled.service

# Create the required environment file
echo 'PORT=
FLAGS=
' | sudo tee /etc/default/tailscaled

# Create state and runtime directories
sudo mkdir -p /var/lib/tailscale /var/run/tailscale

# Symlink binary to the path the service expects
sudo ln -sf /usr/local/bin/tailscaled /usr/sbin/tailscaled

# Start the daemon
sudo systemctl daemon-reload
sudo systemctl start tailscaled
```

**Authenticate** (headless — use `--operator` to avoid root for subsequent CLI use):

```bash
sudo tailscale up --operator=$USER
# Visit the printed URL in a browser
# After auth, verify:
tailscale status
tailscale ip -4     # your tailnet IP, e.g. 100.x.x.x
```

### 2. Generate a GPG Key

Non-interactive batch mode (ed25519 signing + cv25519 encryption):

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

# Get the key ID:
gpg --list-secret-keys --keyid-format=long
# Look for: sec   ed25519/XXXXXXXXXXXX 2026-07-23 [SCA]
# Key ID is the hex after the slash
```

**Critical: Set `PASSWORD_STORE_DIR` to an absolute path.** The `$HOME` variable may point to a Hermes profile fake home (e.g. `{profile_home}/`). The password store and GPG homedir will follow `$HOME`, placing them inside the profile instead of the real home. Fix:

```bash
export PASSWORD_STORE_DIR="{user_home}/.password-store"
echo 'export PASSWORD_STORE_DIR="{user_home}/.password-store"' >> {user_home}/.bashrc
```

### 3. Install pass

```bash
sudo apt-get install -y pass pass-extension-otp

# Initialize the store
pass init "<GPG_KEY_ID>"    # replace with your GPG key ID

# Set editor
export EDITOR="/snap/bin/code --wait"   # or nano, vim, etc.
echo 'export EDITOR="/snap/bin/code --wait"' >> ~/.bashrc
```

### 4. Set Up Git Sync

The sync model is **git over Tailscale SSH** — one device hosts a bare repo as the origin.

**On the origin device (this machine):**

```bash
# Initialize git in the password store
pass git init
git branch -m master main    # rename branch to match conventions
git config user.name "Your Name"
git config user.email "you@example.com"

# Create a bare repo as local origin (switch to tailnet path later)
mkdir -p ~/{pass-bare-repo}
cd ~/{pass-bare-repo} && git init --bare
cd ~/.password-store
git remote add origin ~/{pass-bare-repo}
git push -u origin main
```

Once you have the tailnet IP (`tailscale ip -4`), change the remote to the tailnet path:

```bash
cd ~/.password-store
git remote set-url origin {user}@100.x.x.x:{user_home}/{pass-bare-repo}
```

**On each additional device:**

```bash
# Install pass + GPG + import the public key
gpg --import /tmp/pubkey.asc
gpg --edit-key <KEY_ID> trust

# Clone the password store
git clone {user}@<origin-tailnet-ip>:{user_home}/{pass-bare-repo} ~/.password-store

# Or if origin uses local path:
git clone {user_home}/{pass-bare-repo} ~/.password-store

# Set the remote to the tailnet path:
cd ~/.password-store
git remote set-url origin {user}@<origin-tailnet-ip>:{user_home}/{pass-bare-repo}
```

### 5. Install browserpass

```bash
# Firefox native host (via apt):
sudo apt install webext-browserpass

# Chrome/Chromium native host (separate config):
sudo mkdir -p /etc/opt/chrome/native-messaging-hosts
cat > /tmp/browserpass-chrome.json << 'JSON'
{
    "name": "com.github.browserpass.native",
    "description": "Browserpass native component for the Chrome extension",
    "path": "/usr/lib/browserpass/browserpass-native",
    "type": "stdio",
    "allowed_origins": [
        "chrome-extension://jkdmgdpkkggjhjckkpdgccokejgmdoeg/"
    ]
}
JSON
sudo cp /tmp/browserpass-chrome.json /etc/opt/chrome/native-messaging-hosts/com.github.browserpass.native.json
```

Then install the browser extension:
- **Chrome/Edge:** [Chrome Web Store → browserpass](https://chromewebstore.google.com/detail/browserpass/jkdmgdpkkggjhjckkpdgccokejgmdoeg)
- **Firefox:** [AMO → browserpass](https://addons.mozilla.org/firefox/addon/browserpass/)

### 6. Add Credentials

```bash
# From clipboard/stdin:
echo "cfat_xxxxxxxxxxx" | pass insert --echo infra/cloudflare-api-token

# Interactive (opens editor):
pass edit infra/cloudflare-api-token

# Auto-generate a password:
pass generate hermes/openrouter-key 32

# Add multi-line entry (URL, username, password, notes):
pass insert --multiline services/example
```

### 7. Hermes Integration

**Option A — Shell function for startup:**

```bash
# In ~/.bashrc or a startup script
export CLOUDFLARE_TOKEN=$(pass show infra/cloudflare-api-token)
export SUPABASE_PAT=$(pass show infra/supabase-personal-access-token)
```

**Option B — On-demand in cron/scripts:**

```bash
pass show infra/cloudflare-api-token | head -1
```

## Daily Operations

```bash
# Add a credential (auto-commits to git)
pass insert infra/new-key

# Sync to other devices
pass git push
pass git pull

# Retrieve
pass show infra/cloudflare-api-token
pass -c infra/cloudflare-api-token   # copy to clipboard (clears after 45s)

# List all
pass ls

# Edit
pass edit infra/cloudflare-api-token
```

## Benefits Over Alternatives

| Aspect | age + git | pass | Bitwarden SM (cloud) |
|--------|-----------|------|----------------------|
| Browser autofill | ❌ | ✅ browserpass | ✅ Bitwarden ext |
| Structured CLI (insert/edit/generate) | ❌ manual encrypt | ✅ native | ✅ bws CLI |
| Auto-commit on mutation | ❌ manual git | ✅ | ✅ server |
| Mobile access | ❌ | ✅ Password Store (Android) | ✅ |
| Data sovereignty | ✅ your devices | ✅ your devices | ❌ Bitwarden cloud |
| Hermes-native | ❌ shell wrap | ❌ shell wrap | ✅ `hermes secrets bw` |

## Pitfalls

- **GPG key backup is critical.** If you lose the private key, the entire store is unrecoverable. Back up immediately:
  ```bash
  gpg --export-secret-keys -a > ~/backup/gpg-private-key.asc
  chmod 400 ~/backup/gpg-private-key.asc
  ```
- **$HOME may point to a Hermes profile path.** Always use absolute paths for `PASSWORD_STORE_DIR` — verify with `echo $HOME` before initializing.
- **Tailscale systemd service** — the tarball's `tailscaled.service` references `--port=${PORT}` which breaks with empty vars. Always patch to `--port=0` and create `/etc/default/tailscaled`.
- **`pass git push` branch name** — git's default branch is `master` but you likely want `main`. Rename immediately: `git branch -m master main` before the first push.
- **browserpass requires both native host AND browser extension.** The native host lives at `/usr/lib/browserpass/browserpass-native`. The extension talks to it via native messaging. Both are required.
- **Chrome extension ID is `jkdmgdpkkggjhjckkpdgccokejgmdoeg`** — this must match `allowed_origins` in the Chrome native messaging host JSON.
- **Headless/agent devices** need a Tailscale auth key: `sudo tailscale up --authkey=tskey-auth-xxxxx`
- **Password Store (Android)** reads the same `.gpg` files. Sync via Tailscale + git, or use Syncthing to replicate the `.password-store/` directory.
