# Supabase Schema Setup via Management API

## Problem
You need to run DDL (CREATE TABLE, ALTER, etc.) on a Supabase project but:
- The database is IPv6-only and your machine lacks IPv6 connectivity (common on VPS/cloud hosts)
- `psql` / `psycopg2` / Supabase CLI direct connections fail with "Network is unreachable" or timeout
- The connection pooler also rejects the tenant identifier

## Solution
Use the Supabase Management API's SQL query endpoint. This works over standard HTTPS and handles any connectivity issue.

## Prerequisites
- A Supabase **Personal Access Token** (`sbp_...`). Generate this at:
  Supabase Dashboard → Settings → API → Personal Access Tokens → Create token

## Endpoint
```
POST https://api.supabase.com/v1/projects/{project-ref}/database/query
```

## Critical: Dollar-Quoting for String Literals

The Management API's SQL endpoint strips **single quotes** (`'`) from queries. You cannot use `'public'` or `'core'` or any standard SQL string literal — it will fail with:
```
ERROR: 0A000: cannot use column reference in DEFAULT expression
LINE 3: tier TEXT DEFAULT core,
```

**Fix:** Use PostgreSQL dollar-quoting (`$$...$$`) instead of single quotes for all string literals:

```sql
-- ❌ Will fail (single quotes stripped by API)
CREATE TABLE clients (
    tier TEXT DEFAULT 'core',
    status TEXT DEFAULT 'onboarding'
);

-- ✅ Works (dollar-quoting survives API parsing)
CREATE TABLE clients (
    tier TEXT DEFAULT $$core$$,
    status TEXT DEFAULT $$onboarding$$
);
```

This applies to:
- `DEFAULT` values for text columns
- `WHERE table_schema = 'public'` → `WHERE table_schema = $$public$$`
- Any SQL string comparison value
- You do NOT need to change the SQL syntax inside `$$...$$` — it behaves identically to single-quoted strings in PostgreSQL

## Full Workflow

```bash
# 1. Store the PAT
export PAT="sbp_your_personal_access_token_here"
export REF="your_project_ref"  # from project URL: https://supabase.com/dashboard/project/{ref}

# 2. Create a migration SQL file (use dollar-quoting!)
cat > schema.sql << 'SQL'
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    tier TEXT DEFAULT $$core$$
);
SQL

# 3. Execute via Management API
curl -s -X POST "https://api.supabase.com/v1/projects/${REF}/database/query" \
  -H "Authorization: Bearer ${PAT}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg q "$(cat schema.sql)" '{"query": $q}')"

# 4. Verify tables
curl -s -X POST "https://api.supabase.com/v1/projects/${REF}/database/query" \
  -H "Authorization: Bearer ${PAT}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT table_name FROM information_schema.tables WHERE table_schema = $$public$$ ORDER BY table_name;"}'
```

## Verify the PAT Works First

Before running DDL, confirm the PAT is valid:

```bash
curl -s "https://api.supabase.com/v1/projects" \
  -H "Authorization: Bearer ${PAT}"
```

This should return a JSON array of your projects. If it returns `{"message":"JWT could not be decoded"}`, the token format is wrong or expired.

## Alternatives When This Fails

| Option | How | When |
|---|---|---|
| **Supabase Dashboard SQL Editor** | Paste SQL into the browser SQL Editor and click Run | Quickest, requires human logged into Supabase |
| **Supabase CLI with PAT** | `export SUPABASE_ACCESS_TOKEN="$PAT" && npx supabase link --project-ref $REF --password "$DB_PASS"` then push migrations | If project is linkable (needs DB password) |
| **psql with IPv6** | If your machine has IPv6, connect directly | Rare — most cloud VPS don't have IPv6 |

## Why This Happens

The `/v1/projects/{ref}/database/query` endpoint is designed for quick queries from the Supabase dashboard UI (like the SQL Editor's "run" button). It has a custom query parser that normallizes single-quote-delimited values differently than PostgreSQL's native parser. Dollar-quoting bypasses this normalization.
