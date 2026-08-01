# Fine-Grained GitHub PAT Limitations

## Problem

GitHub now defaults to **fine-grained personal access tokens** (not classic PATs) for new tokens. Fine-grained PATs have scoped permissions per-repo or per-org, but they **cannot accept organization membership invitations via the API**.

**Attempting to accept an org invitation with a fine-grained PAT:**

```bash
# ❌ Returns 403
gh api -X PATCH /user/memberships/orgs/OrgName -f state=active
# → "Resource not accessible by personal access token"
```

## Root Cause

Fine-grained PATs use a different authorization model than classic PATs. They don't have `admin:org` scope access — org membership acceptance requires web-session context or a classic PAT with `admin:org`.

## Workaround

1. **Find the invitation email** via himalaya or ask the user to forward it
2. The user (or the invited account's owner) clicks the invitation link in the browser:
   `https://github.com/orgs/OrgName/invitation?via_email=1`
3. Once accepted, the fine-grained PAT works normally for all repo operations within the org

## Detection

Check if your token is fine-grained:

```bash
curl -sI -H "Authorization: Bearer $(gh auth token)" \
  https://api.github.com/rate_limit 2>&1 | \
  grep -i "x-accepted-github-permissions"
# If this header is present → fine-grained
```

## Validation

| Operation | Fine-Grained PAT | Classic PAT (`admin:org`) |
|-----------|-----------------|---------------------------|
| Read/write repos (personal + org collab) | ✅ | ✅ |
| PRs, issues, actions | ✅ | ✅ |
| Accept org invites | ❌ | ✅ |
| **Transfer repos to org** | ❌ _403: Resource not accessible_ | ✅ |
| **Create repos under org** | ❌ _403: You need admin access_ | ✅ |
| Manage org settings | ❌ | ✅ |
| Org secrets | ✅ (if permitted) | ✅ |

## Workaround for Repo Transfer / Creation

When a fine-grained PAT blocks moving content into an org:

1. Ask the user to create the target repo manually via browser at `https://github.com/orgs/ORG_NAME/repositories/new` — make it private, skip README/gitignore/license (content already exists)
2. Add the new repo as a secondary remote:
   ```bash
   git remote add org https://github.com/ORG_NAME/repo-name.git
   git push org main
   ```
3. Optionally remove the old remote once confirmed:
   ```bash
   git remote remove origin
   git remote rename org origin
   ```

## When to Ask for a Classic PAT

If the task requires org management (creating org repos, accepting invites, managing org settings) and only a fine-grained PAT is available, ask the user to:
- Accept the invitation via web UI **OR**
- Generate a classic PAT at https://github.com/settings/tokens with `admin:org` scope
