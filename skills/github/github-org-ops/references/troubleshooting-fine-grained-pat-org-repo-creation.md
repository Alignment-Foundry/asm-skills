# Troubleshooting: Fine-Grained PAT → Org Repo Creation

## Symptom

`gh repo create alignment-foundry/repo --public` fails with:

```
GraphQL: {dev_account} does not have the correct permissions to execute `CreateRepository` (createRepository)
```

Rest API (curl) fails with:

```
ERROR: You need admin access to the organization before adding a repository to it.
```

## Root Cause

The fine-grained PAT (`github_pat_...`, ~93 chars) exists, authenticates successfully, and the user IS a member of the org — but the PAT hasn't been **authorized** at the org level for repo creation.

Three distinct checkpoints along the credential chain:

| Check | Pass/Fail |
|---|---|
| `gh auth status` | ✅ OK |
| `gh api user` | ✅ Returns user login |
| `GH_TOKEN=$(gh auth token)` | ✅ Returns `github_pat_...` (93 chars) |
| `curl /user` | ✅ Returns user profile |
| `curl /orgs/Alignment-Foundry` | ✅ Returns org info (token can *see* the org) |
| `curl /orgs/X/repos POST` | ❌ "You need admin access" |
| `gh repo create org/repo` | ❌ Permission error |

The token can *read* user and org data but hasn't been granted **repository creation** for that org.

## Diagnostic Script

```bash
# Run this when gh repo create fails for an org
echo "=== 1. Token Info ==="
TOKEN=$(gh auth token 2>/dev/null)
echo "Prefix: ${TOKEN:0:12}...  Length: ${#TOKEN}"

echo "=== 2. Credential File Locations ==="
for f in \
  {user_home}/.git-credentials \
  ~/.git-credentials; do
  if [ -f "$f" ]; then
    echo "EXISTS: $f"
    echo "Content: $(head -1 "$f" | cut -d: -f1,2)***"
  else
    echo "MISSING: $f"
  fi
done

echo "=== 3. Test Auth ==="
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/user | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'User: {d.get(\"login\",\"FAIL\")}')"

echo "=== 4. Test Org Access ==="
curl -s -H "Authorization: token $TOKEN" \
  https://api.github.com/orgs/Alignment-Foundry | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'Org: {d.get(\"login\",\"NO ACCESS\")}')"

echo "=== 5. Try Create ==="
curl -s -X POST \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/orgs/Alignment-Foundry/repos \
  -d '{"name":"asm-skills","description":"test","private":false,"auto_init":false}' \
  | python3 -c "
import sys, json
resp = json.load(sys.stdin)
if 'full_name' in resp:
    print(f'SUCCESS: {resp[\"full_name\"]}')
elif 'message' in resp:
    print(f'FAIL: {resp[\"message\"]}')
else:
    print(str(resp)[:300])
"
```

## Fix: Org-Level PAT Authorization

The PAT owner or an org admin must authorize the PAT at:

**GitHub → `<org>` → Settings → Personal access tokens → Approve**

Or the PAT can be created directly from the org settings page to ensure it has the right scope from the start:

**`https://github.com/organizations/<org>/settings/personal-access-tokens`**

Required permissions for repo creation:
- **Repository access**: "All repositories" (or specific repos)
- **Permissions → Administration**: Read (minimum) or Write (to create)

## Why Not `gh repo create`

When the PAT lacks org repo creation scope, `gh repo create org/repo` fails with the GraphQL error above. The `gh` CLI uses the PAT the user's session was created with — there's no `--token` flag to inject a different one per invocation. To use a different PAT, set `GH_TOKEN` in the environment:

```bash
export GH_TOKEN="github_pat_<org-authorized-token>"
gh repo create alignment-foundry/repo --public
```

## Historical Context

This exact scenario was encountered Jul 28, 2026: the `{dev_account}` account had a fine-grained PAT (`github_pat_...`, stored in the Hermes alpha profile's `~/.git-credentials`), was a member of `Alignment-Foundry`, but the PAT had never been authorized at the org level. The token worked for user-level API calls but rejected org repo creation.
