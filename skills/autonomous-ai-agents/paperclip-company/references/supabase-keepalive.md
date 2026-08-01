# Supabase Free-Tier Keep-Alive

## Problem

Supabase free-tier projects are **paused after 7 days of inactivity**. A paused project can be manually restored via the dashboard, but any databases, auth users, and storage objects are inaccessible during the downtime. This is a common issue for early-stage startups running on free plans.

Prevention: perform a lightweight query at least every **5-6 days** (every 3 days provides a safety margin).

## Solutions

### Option A: Supabase REST API (simplest — no PAT needed)

The Supabase REST API accepts a minimal ping — no DB query needed, just a URL hit:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  "https://<project-ref>.supabase.co/rest/v1/" \
  -H "apikey: <anon-public-key>"
```

A `200` or `404` response means the project is alive. Only a `5xx` or timeout indicates a paused/evicted project.

### Option B: Management API SQL endpoint (relies on `sbp_` PAT)

Runs `SELECT 1` through the Supabase Management API:

```bash
export PAT="sbp_..."
export REF="your-project-ref"  # first segment of supabase.co subdomain

curl -s -X POST "https://api.supabase.com/v1/projects/${REF}/database/query" \
  -H "Authorization: Bearer ${PAT}" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT 1 AS alive;"}'
```

Expected success response: `[{"alive":1}]`

### Option C: Direct psql (requires IPv6 on host)

```bash
export PGPASSWORD="<db-password>"
psql -h "db.<project-ref>.supabase.co" -p 5432 -U postgres -d postgres -c "SELECT 1"
```

Many VPS/cloud hosts lack IPv6 connectivity, making this fail with `Network is unreachable`.

## Implementation in a Paperclip Company

### As a Cron Job (recommended for zero-agent-budget infra)

Create a Hermes cron job (`no_agent=true`, script-based) that runs every 3 days:

```bash
#!/usr/bin/env bash
# Hermes script at ~/.hermes/scripts/supabase-keepalive.sh
# Triggered by cron every 3 days, no_agent=true
# Only outputs on failure (watchdog pattern)

NOW=$(date '+%Y-%m-%d %H:%M:%S')
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "https://<project-ref>.supabase.co/rest/v1/" \
  -H "apikey: <anon-key>" \
  --max-time 10)

if [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
  echo "[$NOW] ALERT: Supabase keep-alive ping failed — project may be paused"
  exit 1
elif [ "$HTTP_CODE" -ge 500 ]; then
  echo "[$NOW] WARN: Supabase returned $HTTP_CODE — project may be in recoverable state"
  exit 1
fi
# Silent on success — watchdog pattern
exit 0
```

Cron schedule: `0 12 */3 * *` (noon, every 3rd day).

### As a Paperclip Agent Task (uses agent budget, adds audit trail)

Create a recurring issue via Paperclip API assigned to the **Founding Engineer**:

```bash
curl -s -X POST "http://localhost:3100/api/companies/${COMPANY_ID}/issues" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Supabase keep-alive ping",
    "description": "Ping Supabase REST API to prevent free-tier pause after 7 days inactivity.\n\ncurl -s -o /dev/null -w \"%{http_code}\" \"https://<project-ref>.supabase.co/rest/v1/\" -H \"apikey: <anon-key>\"",
    "assigneeAgentId": "<founding-engineer-agent-id>",
    "priority": "medium"
  }'
```

Schedule via a Hermes cron job that creates this issue every 3 days, or set a Paperclip agent heartbeat at 72-hour intervals.

## Which Method to Choose

| Method | Cost | Reliability | Complexity |
|--------|------|-------------|------------|
| REST API ping (cron + curl, no_agent=true) | 0 tokens | High (HTTPS) | Very low |
| Management API SQL (cron + curl, no_agent=true) | 0 tokens | High (HTTPS) | Low (needs PAT) |
| Paperclip agent heartbeat | Agent budget consumed | High | Medium |
| Direct psql | 0 tokens | Low (IPv6) | Low |

**Recommendation:** Use the REST API ping as a `no_agent=true` Hermes cron job — zero agent cost, HTTPS-reliable, no secrets exposure risk if the anon key is used (it's public by design).