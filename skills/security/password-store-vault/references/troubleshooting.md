# pass / GPG Troubleshooting Reference

Key diagnostic commands for when `pass show` or `pass -c` fails.

## Error: "public key decryption failed: No secret key"

**Meaning:** GPG found the public key for decryption, but the corresponding private (secret) key is not in the keyring GPG is currently using.

**Diagnosis:**

```bash
# Check which homedir GPG is actually using
gpgconf --list-dirs | grep homedir

# List secret keys in that homedir
gpg --list-secret-keys --keyid-format=long

# Compare with what the password store expects
cat ~/.password-store/.gpg-id

# Check if there's a second keyring elsewhere
ls -la ~/.gnupg/private-keys-v1.d/
gpg --homedir /path/to/other/.gnupg --list-secret-keys
```

**Common cause in Hermes:** The GPG key was created inside a Hermes profile session where `$HOME` points to `/home/user/.hermes/profiles/<name>/home/`. GPG stores the private key at `<profile-home>/.gnupg/private-keys-v1.d/`, not at the real `~/.gnupg/`. When running `pass` in a normal terminal, GPG looks at the real `~/.gnupg/` and finds no secret key.

**Fix — backup old keyring and replace:**

```bash
# 1. Backup the (likely empty/stale) real home keyring
cp -a ~/.gnupg ~/.gnupg.backup.$(date +%Y)

# 2. Replace with the Hermes profile's live keyring
#    (find the profile homedir first via gpgconf --list-dirs from inside Hermes)
rm -rf ~/.gnupg
cp -a /home/user/.hermes/profiles/<profile>/home/.gnupg ~/.gnupg

# 3. If the profile's .gnupg doesn't have private-keys-v1.d/ (public key only),
#    the private key files may be orphaned in the backup:
cp -a ~/.gnupg.backup.*/private-keys-v1.d ~/.gnupg/

# 4. Verify
gpg --list-secret-keys --keyid-format=long
```

## Error: "public key decryption failed: Timeout"

**Meaning:** The secret key IS present in the keyring, but GPG's pinentry program can't prompt for the passphrase. This happens when `pinentry-gnome3` is the default but there's no X11 display (e.g., SSH, TUI, headless terminal).

**Diagnosis:**

```bash
# Check which pinentry is default
update-alternatives --display pinentry

# Check gpg-agent config
cat ~/.gnupg/gpg-agent.conf
```

**Fix:**

```bash
# Option A: Per-user gpg-agent config (no sudo needed)
cat > ~/.gnupg/gpg-agent.conf << 'EOF'
pinentry-program /usr/bin/pinentry-curses
default-cache-ttl 3600
max-cache-ttl 86400
EOF

# Reload the agent
gpg-connect-agent reloadagent /bye

# Option B: System-wide (requires sudo)
sudo update-alternatives --set pinentry /usr/bin/pinentry-curses
```

## Error: "public key decryption failed: No passphrase given"

**Meaning:** The key is recognized and pinentry is working, but you're using `--pinentry-mode loopback` with an empty/incorrect passphrase. The key has a passphrase set and you need to supply it, either via interactive pinentry or loopback.

**Fix:** Run `pass show some/entry` interactively once to cache the passphrase:

```bash
# This prompts for the passphrase (via pinentry-curses), then caches it
pass show infra/cloudflare-account-id

# After that, subsequent commands reuse the cached passphrase
pass -c work/stripe/secret-key-live
```

## GPG Agent Management

```bash
# Check running agents
ps aux | grep gpg-agent

# See agent socket locations
ls -la /run/user/$(id -u)/gnupg/

# Reload agent config (picks up gpg-agent.conf changes)
gpg-connect-agent reloadagent /bye

# Kill and restart (for a clean state)
gpgconf --kill gpg-agent
gpgconf --launch gpg-agent

# Check cache TTL (from current config)
gpgconf --list-options gpg-agent | grep cache
```

## Key Structure (GPG 2.2+)

```
~/.gnupg/
├── pubring.kbx              ← Public keys (visible to --list-keys / --list-secret-keys)
├── trustdb.gpg              ← Trust level database
├── private-keys-v1.d/       ← Private key material (individual .key files per keygrip)
│   ├── <keygrip1>.key       ← Signing key (ed25519)
│   └── <keygrip2>.key       ← Encryption subkey (cv25519)
├── gpg-agent.conf           ← Agent configuration
├── openpgp-revocs.d/        ← Revocation certificates
└── random_seed              ← Entropy cache
```

A `pubring.kbx` with a public key entry but no matching `.key` file in `private-keys-v1.d/` = public key visible but decryption impossible ("No secret key").

## Quick Connectivity Test

```bash
# Is the key installed and usable?
echo "test" | gpg -e -r "$(cat ~/.password-store/.gpg-id)" 2>&1 | gpg -d 2>&1

# Does pass work?
PASSWORD_STORE_DIR="$HOME/.password-store" pass ls
PASSWORD_STORE_DIR="$HOME/.password-store" pass show infra/cloudflare-account-id
```
