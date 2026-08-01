# Git History Cleanup with git-filter-repo

When credentials, PII, or personal paths have been committed to a repo (even briefly), **deleting the current file is NOT enough** — the old data lives in every commit that touched it. Anyone can `git log -p` and see the full history. Use `git-filter-repo` to rewrite history so the sensitive data never existed.

## When to Use

- During pre-publish audit, you find credentials/PII in files that were already committed
- A user asks you to sanitize git history retroactively
- You pushed a commit with sensitive data and need to clean it before others clone

## Prerequisites

```bash
pip install git-filter-repo
```

Installs a `git-filter-repo` binary that `git` picks up automatically (run as `git filter-repo`).

## Workflow

### 1. Identify Sensitive Strings

Search all commits:

```bash
git log --all -p -S "sensitive_string" -- .
```

### 2. Create Replacements File

Each line: `old_text==>new_text`. **Longest matches first** to avoid substring interference:

```
/path/with/longer/prefix/==>{placeholder}/
/path/with/==>{placeholder}/
sensitive-account==>{account}
```

### 3. Run filter-repo

```bash
git filter-repo \
  --replace-text /tmp/replacements.txt \
  --name-callback '
if name == b"Original Author": return b"Pseudonym"
return name
' \
  --email-callback '
if email.endswith(b"@personal.com"): return b"user@example.com"
return email
' \
  --force
```

### 4. Verify

```bash
git log --all -p -S "old-sensitive-string" -- .   # should be empty
git log --format="%an <%ae>" | sort -u             # check author info
python3 scripts/audit-credentials.py               # run repo scanners
```

### 5. Re-add Remote and Force Push

filter-repo removes the origin remote automatically:

```bash
git remote add origin https://github.com/owner/repo.git
GH_TOKEN=$(python3 -c "
with open(os.path.expanduser('~/.git-credentials')) as f:
    line = f.readline().strip()
import re
m = re.match(r'https://[^:]+:([^@]+)@', line)
if m: print(m.group(1), end='')
")
git push --force "https://<user>:<token>@github.com/owner/repo.git" main
git remote set-url origin https://github.com/owner/repo.git
```

**⚠️ Force-push rewrites shared history.** Coordinate with collaborators.

## Path Obfuscation Rules

| Personal detail | Replace with |
|----------------|-------------|
| `/home/realuser/` | `{user_home}/` |
| `/home/realuser/.hermes/` | `{hermes_home}/` |
| `.hermes/profiles/profilename/` | `{profile}/` |
| `.hermes/profiles/profilename/home/` | `{profile_home}/` |
| GitHub dev account | `{dev_account}` |
| Personal venv name | `{email_venv}` |

**Do NOT replace** public domains (`example.com`), generic example paths (`.bashrc`), placeholders (`user@gmail.com`), or service domains (`imap.gmail.com`).

## Pitfalls

- **Replacements apply sequentially** — put `/home/u/.x/` BEFORE `/home/u/` in the file
- **Handle trailing-slash variants** — both `/home/u/` and standalone `/home/u` need entries
- **Author email is metadata, not content** — use `--email-callback`, not `--replace-text`
- **filter-repo removes origin** — must re-add after running
- **Clean working tree required** — commit or stash first
- **Can be re-run** — if you missed a pattern, add it and re-run
