---
name: github-org-ops
description: "Cross-organization GitHub operations — repo migration, PAT authorization across orgs, fine-grained token management."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Organizations, Migration, PAT, Repositories]
    related_skills: [github-repo-management, github-auth]
---

# GitHub Cross-Org Operations

Operations that cross GitHub org boundaries: migrating repos between orgs, authorizing fine-grained PATs, and handling permission boundary issues.

## When to Use This Skill

The standard `github-repo-management` skill covers single-org workflows (clone, create, fork within your own account). This skill covers **boundary-crossing** operations:

- Migrating a repo from one org to another
- Creating repos in a target org when your PAT is tied to a different account
- Handling fine-grained PATs that lack org-level repo creation scope

## Core Pattern: Repo Migration Without `gh repo transfer`

The `gh repo transfer` command may be unavailable (older GH CLI). The fallback is:

1. Create the target repo in the destination org via API
2. Push the local code to the new remote
3. Clean up remotes and update tracking

### Step 1 — Get a Working PAT for the Target Org

Fine-grained PATs require explicit org authorization. If `gh repo create TargetOrg/repo` fails, two possible error messages signal the same root cause:

```
does not have the correct permissions to execute `CreateRepository`
```

```
You need admin access to the organization before adding a repository to it.
```

Both mean: the PAT exists but hasn't been authorized at the org level.

### Diagnostic — Check What the Current Token Can Do

Before assuming the user lacks access, run these checks to understand the actual gap:

```bash
GH_TOKEN=$(gh auth token 2>/dev/null)

# 1. What kind of token is it?
echo "Token prefix: ${GH_TOKEN:0:12}..."
echo "Token length: ${#GH_TOKEN}"
# github_pat_... (93 chars) = fine-grained PAT
# ghp_... (40 chars) = classic PAT

# 2. Does the token authenticate at all?
curl -s -H "Authorization: token $GH_TOKEN" \
  https://api.github.com/user | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'User: {d.get(\"login\",\"FAIL\")}')"

# 3. Can the token see the target org?
curl -s -H "Authorization: token $GH_TOKEN" \
  https://api.github.com/orgs/<target-org> | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Org: {d.get(\"login\",\"? check response\")}')"

# 4. Check credential locations
for f in \
  ~/.git-credentials \
  {user_home}/.git-credentials \
  ~/.git-credentials; do
  if [ -f "$f" ]; then
    echo "CREDS: $f (exists)"
    head -1 "$f" | cut -d: -f1,2
  fi
done
```

A token that authenticates (`/user` succeeds) and sees the org (`/orgs/X` returns data) but fails on repo creation needs org-level authorization.

### Fix Options

- **User creates the repo manually** at `github.com/organizations/<org>/repositories/new` (30s)
- Or the user provides a PAT that was granted the necessary org permissions

### Step 2 — Create Target Repo via API

```bash
curl -s -X POST \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/orgs/<target-org>/repos \
  -d '{"name":"<repo>","description":"<desc>","private":true,"auto_init":false}'
```

Check the response for `"full_name": "<org>/<repo>"` — any error message means the PAT lacks permissions.

### Step 3 — Push Code

```bash
cd /path/to/local/repo

# Embed PAT in URL for auth (one-shot)
git remote set-url origin https://<PAT>@github.com/<org>/<repo>.git
git push -u origin main

# Restore clean URL after push
git remote set-url origin https://github.com/<org>/<repo>.git
```

### Step 4 — Handle Branch Name Mismatch

If local uses `master` and new repo expects `main`:

```bash
git push -u origin master
git branch -m master main
git push origin main
git push origin --delete master

# Update default branch on GitHub
curl -s -X PATCH \
  -H "Authorization: Bearer <PAT>" \
  https://api.github.com/repos/<org>/<repo> \
  -d '{"default_branch":"main"}'
```

### Locate the Right `.git-credentials` File

Under a Hermes profile with a fake `$HOME`, `~/.git-credentials` resolves to the profile directory, not the real home. The active credential file lives at the profile's home:
```bash
# The active one (inside the Hermes profile)
cat ~/.git-credentials

# The real home's (no profile effect)
cat {user_home}/.git-credentials
```

Only the one under the active profile's home is used by `git` and `gh`. Check both when searching for stored tokens:
```bash
find {user_home}/ -maxdepth 4 -name '.git-credentials' -type f 2>/dev/null
```
See [`github-auth`](skill:github-auth) for extraction patterns.

### Step 5 — Save PAT to git-credentials (Optional)

```bash
# Replace the existing github.com entry in ~/.git-credentials
sed -i 's|https://[^:]*:.*@github.com|https://<user>:<PAT>@github.com|' ~/.git-credentials
```

Or add the specific org as a credential:

```bash
echo "https://<user>:<PAT>@github.com" >> ~/.git-credentials
chmod 600 ~/.git-credentials
```

### Step 6 — Update Project Tracking

Update `PROGRESS.md` frontmatter `repo:` field and CATALOG.md last-action date.

## Verification

After migration, confirm:

```bash
# Check remote is correct
git remote -v

# Verify push works
git fetch origin

# Confirm on GitHub via API
curl -s -H "Authorization: Bearer <PAT>" \
  https://api.github.com/repos/<org>/<repo> \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d[\"full_name\"]} — {\"private\" if d[\"private\"] else \"public\"} — {d[\"default_branch\"]}')"
```

## Pitfalls

- **`gh repo transfer`** doesn't exist in older GH CLI versions — always have the curl fallback ready
- **Fine-grained PATs** require org-level approval even if the PAT has all the right permissions on paper — the user must authorize it at the org settings page. The error `"You need admin access to the organization before adding a repository to it."` means the PAT exists and authenticates but hasn't been authorized at the org level. Use the diagnostic flow in Step 1 to distinguish this from "no token at all."
- **`~/.git-credentials`** resolves under Hermes profile's fake `$HOME` (e.g. `{profile_home}/`) — check that path specifically, not the real `{user_home}/.git-credentials`, which may be empty or absent even when git operations work
- **`grep` on `~/.git-credentials` with empty HOME** — before running grep-based token extraction, verify the credential file actually exists at the resolved path. A missing file with `set -e` can silently abort a script block
- **Token in URL** persists in shell history — clean the remote URL after push
- **Default branch mismatch** between local (`master`) and GitHub default (`main`) requires the API `default_branch` PATCH — pushing `main` alone won't change GitHub's default
