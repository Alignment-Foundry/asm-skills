# Worked Example: Paperclip Company Setup

Complete worked example from a real business design session (v3.2 — Startup Stack / Claude Model Stack).
Use as a template when setting up any new Paperclip company.

## Company

| Field | Value |
|---|---|
| Name | Example Services |
| Mission | Deliver async operational clarity to independent small businesses |
| Server | http://127.0.0.1:3100 |
| Mode | local_trusted (private, loopback only) |
| Domain | {business-domain-1} (via Cloudflare) |

## Org Chart

```
The user — Chairman / Board of Directors
  └── Hermes Agent — Chief of Staff (Telegram liaison, Paperclip API interface)
       └── CEO Agent (Paperclip CEO — runs company day-to-day)
            ├── Founding Engineer (builds/maintains startup stack infrastructure)
            ├── Communication Agent (email triage, routing via Resend + GitHub)
            ├── Financial Intelligence Agent (dashboards, narratives via Supabase + Fly.io)
            ├── Document Processing Agent (client documents, data ingestion)
            ├── Operations Agent (weekly ops, churn detection via Supabase + PostHog)
            └── Onboarding Agent (new client intake via Stripe + Clerk + Resend)
```

## Agent Definitions

### CEO Agent
- **Heartbeat:** Daily 9am ET + on-demand when Chief of Staff creates a task
- **Budget cap:** $20/mo
- **Reports To:** Chief of Staff (Hermes Agent)
- **Adapter:** `claude_local` (Claude Code via Claude Max)
- **Model:** Claude Sonnet 5 (strategic reasoning)
- **Responsibilities:** Review agent performance, check escalations, propose strategy, delegate tasks, escalate exceptions to Chief of Staff

### Founding Engineer
- **Heartbeat:** Daily 8am ET (infrastructure health check)
- **Budget cap:** $30/mo
- **Reports To:** CEO Agent
- **Adapter:** `claude_local` (Claude Code via Claude Max)
- **Model:** Claude Sonnet 5 (engineering reasoning)
- **Tools:** Fly.io, Supabase, Cloudflare, Sentry, GitHub, Git
- **On-demand:** Provision Supabase schemas, deploy to Fly.io, configure Cloudflare DNS, wire API integrations, update dashboard templates, resolve incidents

### Communication Agent
- **Heartbeat:** Every 60 min during business hours (8am-6pm ET Mon-Fri)
- **Budget cap:** $15/mo
- **Reports To:** CEO Agent
- **Model:** Claude Haiku (classification + light generation)
- **Tools:** Resend (email), GitHub (template library), Supabase (read-only), PostHog (analytics)
- **Responsibilities:** Check Resend inbox, classify emails (simple/route/escalate/operational), auto-respond from GitHub-hosted templates, log to Paperclip tickets + PostHog

### Financial Intelligence Agent
- **Heartbeat:** Monday 7am ET + 1st of month 7am ET
- **Budget cap:** $30/mo
- **Reports To:** CEO Agent
- **Model:** Claude Sonnet 5 (complex financial reasoning)
- **Tools:** Supabase (read/write financial data), GitHub (dashboard template repo)
- **Responsibilities:** Query Supabase for weekly metrics, generate dashboard commentary (Fly.io-hosted), draft monthly P&L narratives (GitHub for review), quarterly Loom talking points

### Document Processing Agent
- **Heartbeat:** Every 30 min (scan Supabase storage)
- **Budget cap:** $40/mo (includes Fly.io app compute)
- **Reports To:** CEO Agent
- **Model:** Claude Sonnet 5 (long context, multi-document reconciliation)
- **Tools:** Fly.io (processing app), Supabase (storage + DB write), GitHub (schema defs)
- **Responsibilities:** Ingest client documents from Supabase storage, normalize financial exports, write to Supabase tables, flag anomalies via Sentry + Paperclip ticket

### Operations Agent
- **Heartbeat:** Monday 6am ET (weekly)
- **Budget cap:** $10/mo
- **Reports To:** CEO Agent
- **Model:** Claude Haiku (classification + reporting)
- **Tools:** Supabase (read ops data), PostHog (engagement + churn), GitHub (ops dashboard repo)
- **Responsibilities:** Compile weekly MRR/churn/engagement report, push to Fly.io-hosted ops dashboard, flag anomalies via Chief of Staff

### Onboarding Agent
- **Heartbeat:** Event-driven (Stripe webhook) + daily 9am ET check for stalled
- **Budget cap:** $10/mo
- **Reports To:** CEO Agent
- **Model:** Claude Haiku
- **Tools:** Stripe (webhooks), Clerk (auth), Resend (email), Supabase (client data), DocuSign
- **Responsibilities:** Welcome sequence (Resend), Clerk user creation, DocuSign agreement, Supabase client dataset provisioning, Day 7 handoff to Financial Intelligence Agent

## Total Monthly Budget

| Category | Amount |
|---|---|
| All 7 Paperclip agents (budget caps for Claude Max tracking) | $155/mo |
| Startup stack infrastructure (all free tiers at launch) | ~$0/mo → $200-300/mo at scale |
| Paperclip server (self-hosted on local machine) | $0 |
| **Total** | **~$155/mo at launch → ~$355-455/mo at scale** |

At 25 clients × $2,500 avg MRR = $62,500/mo, total costs are under 1% of revenue.

## Startup Stack (Execution Layer)

| Service | Role | Free Tier |
|---|---|---|
| Fly.io | App hosting (dashboard, data intake, doc processing, ops dashboard) | $5-10/mo credits |
| Supabase | PostgreSQL, file storage, auth backend | 500MB DB, 1GB storage, 50K MAU |
| Clerk | Client portal authentication | 10K MAU |
| Stripe | Payments, subscriptions, webhooks | 2.9% + $0.30 |
| Resend | Email delivery (support, dashboards, onboarding) | 500/day, 3K/month |
| PostHog | Analytics, engagement, churn signals | 1M events/month |
| Cloudflare | DNS, SSL, CDN | Unlimited DNS |
| GitHub | Version control, CI/CD, template library | 2K Actions min/month |
| Sentry | Error tracking | 5K events/month |

## Model Strategy

- **Primary:** Claude Sonnet 5 (reasoning agents) + Claude Haiku (classification agents) via Claude Max subscription
- **Future:** Heavy-volume agents may migrate to OpenRouter (GPT, Gemini) or Zen (open-source/SLM) to optimize Claude quota
- **Control mechanism:** Paperclip per-agent budget caps + heartbeat intervals (not dollar-based since Claude Max is flat subscription)

## Governance Routing

| What | Flow |
|---|---|
| New agent hire | CEO proposes → Chief of Staff routes → the user approves |
| Budget override | Agent pauses → CEO escalates → Chief of Staff routes → the user approves |
| Strategy change | CEO proposes → Chief of Staff reviews → the user decides |
| Credential request | CEO needs API key → Chief of Staff asks the user via Telegram → the user provides |
| Weekly briefing | Chief of Staff queries Paperclip API → formats report → sends via Telegram |

## Chief of Staff Telegram Commands

| The User Says | Chief of Staff Does |
|---|---|
| "How's the company doing?" | `GET /api/companies/{id}` + agents list → formatted report |
| "Approve the CEO's budget override" | Paperclip approvals API → confirm |
| "Need to set up a Stripe API key" | Save credential → Paperclip secrets → confirm |
| "What's our spend this month?" | `GET /api/companies/{id}/budgets/overview` → table |
| "Pause the Comms Agent" | `PATCH /api/agents/{id}` → `status: paused` → confirm |
| "Status on founding clients" | `GET /api/companies/{id}/issues?status=todo,done` → list |

## SKILL.md Files

```
company-mission                  → All agents (shared context)
ceo-strategy                      → CEO Agent
founding-engineer-infra           → Founding Engineer
comms-agent-criteria              → Communication Agent
financial-intelligence-metrics    → Financial Intelligence Agent
document-processing-schemas       → Document Processing Agent
operations-reporting              → Operations Agent
onboarding-sequence               → Onboarding Agent
domain-finance-glossary           → All agents (domain reference)
chief-of-staff-operating-model    → Chief of Staff (Hermes — internal)
```

## Build Sequence

1. **Layer 1 (Weeks 1-4):** CEO Agent + Communication Agent. Set up Resend + GitHub template library. Manual email review. Chief of Staff monitors via Telegram.
2. **Layer 2 (Weeks 4-8):** Founding Engineer + Document Processing Agent. Provision Supabase project + schema. Deploy document processing app to Fly.io. Wire external API integrations.
3. **Layer 3 (Weeks 8-16):** Financial Intelligence Agent. Build client dashboard app (Fly.io + Supabase). Wire Clerk auth. Dashboard narratives with CEO Agent review.
4. **Layer 4 (Months 4-6):** Operations Agent + Onboarding Agent. PostHog churn detection. Stripe → Clerk → Resend → Supabase onboarding flow. Sentry error tracking.
5. **Layer 5 (Months 6+):** Auto-send validated narratives. Upstash Redis if queuing needed. Budget audit. SKILL.md refinement from escalation history.
