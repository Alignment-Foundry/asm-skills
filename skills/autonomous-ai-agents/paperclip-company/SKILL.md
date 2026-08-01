---
name: paperclip-company
description: Model any real business as a Paperclip company — org chart, agents, heartbeats, budgets, governance, and Hermes Chief-of-Staff integration via Telegram.
version: 1.5.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [paperclip, orchestration, multi-agent, business-operations, governance]
    category: autonomous-ai-agents
---

# Paperclip Company Skillset

## When to Use

Someone needs to run a real business (not just a coding project) through Paperclip. The pattern applies when:
- A human founder wants AI agents operating under structured governance
- Multiple specialist agents need to coordinate under a lead agent
- The founder needs a Chief of Staff (Hermes) to interface with the Paperclip company via messaging (Telegram, Discord, etc.)
- Budget enforcement, goal alignment, heartbeat schedules, and board-level approvals are required

## Core Architecture Pattern

### Four-Tier Hierarchy

```
Human Founder (Board / Chairman)
  └── Hermes Agent (Chief of Staff — Telegram liaison)
       └── Paperclip CEO Agent (runs company day-to-day)
            ├── Founding Engineer (infrastructure/builds)
            ├── Specialist Agent N... (domain-specific workers)
            └── ...
```

**Tier 1 — Board (Human):**
- Strategic decisions, final approvals (hires, budgets, pricing)
- Quarterly/recurring human-only deliverables (recordings, partnerships)
- Provides credentials when requested (API keys, access grants, payment cards)
- Target: 15-20 hrs/month at scale

**Tier 2 — Chief of Staff (Hermes):**
- Liaison between human and Paperclip company via Telegram DM
- Runs Paperclip API health checks (agent status, budget, spend, escalations)
- Routes account/access/payment requests from CEO Agent to human
- Curates CEO Agent escalations → presents weekly briefing to human
- First-pass triage on all board-level items
- Can pause/resume agents, create tasks, check budgets via Paperclip REST API
- Never needs to open the Paperclip UI for routine operations

**Tier 3 — CEO Agent (Paperclip agent):**
- Daily heartbeat (9am ET recommended) for strategic check-in
- Reviews agent performance metrics from Operations Agent
- Delegates tasks to specialist agents based on workload/capability
- Proposes strategy adjustments → Chief of Staff reviews → Board approves
- Escalates exceptions requiring human judgment
- Reports to Chief of Staff (not directly to human)

**Tier 4 — Specialist Agents:**
- Each has one domain responsibility (communication, financial analysis, data ops, etc.)
- Defined with SKILL.md, heartbeat interval, budget cap, and adapter type
- Reports to CEO Agent
- Never escalates directly to human — always through CEO → Chief of Staff → Board

### Default Specialist Agent Archetypes

These agent types recur across most Paperclip companies. Adapt the responsibilities for the specific domain.

| Agent | Domain | Typical Heartbeat | Budget Range |
|---|---|---|---|
| **Communication Agent** | Email triage, client support, auto-responses | Every 60 min during business hours | $10-15/mo |
| **Financial Intelligence Agent** | Financial narratives, dashboards, reporting | Mon 7am + 1st of month 7am | $25-30/mo |
| **Document Processing Agent** | Data ingestion, normalization, storage | Every 30 min | $25-40/mo |
| **Operations Agent** | MRR, churn, engagement, internal reporting | Mon 6am (weekly) | $10-15/mo |
| Onboarding Agent | New client intake, welcome sequence, setup | Event-driven (webhook) + daily check | $10-15/mo |

### AI-Driven Discovery Methodology

When the business needs market research, ICP language, or competitive positioning but the human founder should not do manual discovery calls (contradicts the async model), use this agent-based discovery pattern:

**Three agents, three responsibilities, fully async:**

| Agent | Schedule | Task | Data Destination |
|---|---|---|---|
| **Communication Agent** | 3x daily (e.g. 6am, 12pm, 6pm) | Scan 8+ source types: LinkedIn industry-specific groups, Reddit (domain-specific subreddits), Twitter/X (#industry tags), trade publication comment sections, competitor websites, industry forums, partner resources. Classify every pain point, phrase, and question found. | `discovery_findings` table in Supabase |
| **Financial Intelligence Agent** | Daily, 1hr after Comms scan | Take raw findings from communication agent. Identify: most common pain points by frequency, recurring verbatim language patterns, objections to the service category, competitor positioning gaps. Output structured analysis. | `discovery_insights` table in Supabase |
| **CEO Agent** | Daily, 1hr after FI analysis | Consolidate findings into: (1) ICP language document with 20+ direct quotes from real sources, (2) positioning validation (does our messaging match market language?), (3) common objections list for FAQ/content, (4) content topic recommendations. Present to Chief of Staff for Board review. | GitHub repo as markdown documents |

**Source types for the Communication Agent to monitor:**

- LinkedIn industry-specific groups, comments on industry-influencer posts
- Reddit: domain-specific subreddits, small business communities
- Twitter/X: industry hashtags, agency owner accounts
- Trade publications: comment sections on relevant articles
- Industry forums: association member discussions, user groups
- Competitor websites: analyze positioning language they use
- Partner/vendor materials: language they use with the target audience

**Async survey (optional fallback):**

If agent discovery hasn't produced sufficient verbatim language by week 4, the CEO Agent can trigger an async email survey:
- 5 short questions, no call required
- Sent via Resend (or equivalent email service)
- Recipients from the human's network
- Responses analyzed by Financial Intelligence Agent
- Only triggered if automated discovery gaps exist

**Success targets:** 100+ raw findings logged, 20+ verbatim quotes extracted, positioning validated against real market language. This replaces human discovery calls entirely.

### Phased Execution Plan Format

For turning a strategy document into executable phases managed by a Paperclip company, use this standardized plan format. Each phase is a self-contained document with these sections:

| Section | Content |
|---|---|
| **Objective** | What this phase achieves for the business |
| **Build tasks** | Table with column: Task, Owner, Deliverable — covers what Founding Engineer + startup stack delivers |
| **Agent tasks** | Table with column: Agent, Heartbeat, Deliverable — what each Paperclip agent executes |
| **Board tasks** | Table with column: Task, Time Budget — what the human does, with estimated hours |
| **Success measures** | Table with column: Measure, Target, How Verified — measurable, verifiable outcomes |
| **Definition of done** | Checkbox checklist — ALL must be checked to advance to next phase |
| **Path to next phase** | Two subsections: "Carries forward" (what stays active) and "Changes" (how the system evolves) |
| **Known unknowns** | Table with column: Question, Assigned To, How We'll Know — risks assigned to specific agents |
| **Budget check** | Table of costs per item with running total vs. budget cap |

For the full template with example content, see the [phased-execution-plan-template.md](./references/phased-execution-plan-template.md) reference file.

All phase documents live under `plan/phase-N.md` in the project directory, with `plan/README.md` serving as the index containing the roadmap timeline, operating rhythm table (daily/hourly/weekly/monthly/quarterly cadence), and escalation path.

The operating rhythm table should cover:
- **Daily:** Agent heartbeat schedules (time-specific: 8am FE, 9am CEO, 60min Comms, 30min Doc Processing)
- **Weekly:** Monday 6am Ops report, 7am FI narratives, 9am dashboard delivery, Chief of Staff brief
- **Monthly:** 1st-of-month narratives, budget review, SKILL.md refinement
- **Quarterly:** Human Loom recording + strategy review
- **Ad hoc:** Board approvals, escalations, partnership conversations via Telegram

The escalation path covers three modes:
1. **Normal operation** — Agent completes heartbeat → CEO reviews → nominal
2. **Exception detected** — Agent flags → CEO triages → Chief of Staff curates → Board decides
3. **Failure mode** — Agent heartbeat fails → FE alerted via Sentry → auto-resolve or escalate

### Startup Stack (Execution Layer)

When the user wants to avoid cloud vendor lock-in and use modern SaaS tools, this is the preferred execution stack:

| Service | Role | Free Tier | Cost at Scale |
|---|---|---|---|
| **Fly.io** | Hosting — dashboard apps, intake forms, processing | $5-10/mo credits | $25-50/mo |
| **Supabase** | PostgreSQL database, file storage, auth backend | 500MB DB, 1GB storage, 50K MAU | $25/mo Pro |
| **Clerk** | User authentication for client-facing portals | 10K MAU free | $25/mo Pro |
| **Stripe** | Payments, subscriptions, webhooks | 2.9% + $0.30 | Processing fees |
| **Resend** | Email delivery — support, dashboards, onboarding | 500/day, 3K/month | $20/mo Growth |
| **PostHog** | Product analytics, engagement, churn signals | 1M events/month | $30/mo Scale |
| **Cloudflare** | DNS, SSL, CDN, email routing | Unlimited DNS, DDoS protection | $20/mo Pro |
| **GitHub** | Version control, CI/CD, template library | 2K Actions min/month | $4/mo Pro |
| **Sentry** | Error tracking, performance monitoring | 5K events/month | $30/mo Team |
| **Upstash** | Redis (queuing, caching, rate limiting at scale) | 10K commands/day | $10/mo Pro |
| **Pinecone** | Vector DB (semantic search, RAG) | 1 pod, 100K vectors | $70/mo Serverless |

Default cost: **~$0/mo at launch** (all free tiers), **~$200-300/mo at scale**.

### Five-Layer Build Sequence

Build each layer until stable before adding the next. Do not automate what you haven't done manually.

| Layer | Weeks | Focus | What Goes Live |
|---|---|---|---|
| **Layer 1** | 1-4 | Communication | CEO Agent + Communication Agent. Manual review of all outbound. |
| **Layer 2** | 4-8 | Data Pipeline | Founding Engineer + Document Processing Agent. Database, file storage, data ingestion. |
| **Layer 3** | 8-16 | Intelligence | Financial Intelligence Agent. Dashboard narratives, reports. Human reviews all. |
| **Layer 4** | 16-24 | Operations | Operations Agent + Onboarding Agent. Churn detection, auto-onboarding, Sentry monitoring. |
| **Layer 5** | 24+ | Optimization | Auto-send validated templates, budget audit, SKILL.md refinement from escalation history. |

### Cost Model (Two-Column)

| Category | Monthly |
|---|---|
| **AI Agent Budget** (Paperclip agent budget caps for Claude Max consumption tracking) | ~$155/mo for 7 agents |
| **Infrastructure** (startup stack SaaS services — all have free tiers at launch) | ~$0/mo at launch → $200-300/mo at scale |
| **Total** | ~$155/mo → ~$355-455/mo |

**Claude Max note:** Paperclip's budget system tracks `billed_cents` (dollar-based caps). Claude Max is a flat subscription, not per-token billing. Control Claude consumption via heartbeat intervals, manual-mode for non-critical agents, and Paperclip's per-agent budget caps as a proxy for usage limits. The $155/mo agent budget is a conservative cap for a 7-agent company — tune based on actual Claude Max quota utilization.

At typical revenue scale ($37.5-45K MRR at 25 clients), total costs are under 1% of revenue. Cost is not the constraint — quality and build discipline are.

### Paperclip Agent Definition Template

```markdown
| Paperclip Field | Value |
|---|---|
| Title | [Director of X] |
| Agent Type | Heartbeat + event-driven |
| Heartbeat Interval | [interval description + cron] |
| Budget | $XX/month |
| Adapter Type | `claude_local` (Claude Code via Claude Max subscription) |
| Model | Claude Sonnet 5 (reasoning-heavy) / Claude Haiku (classification, light generation) |

**Model strategy:** Primary models are Claude (Sonnet 5 for reasoning, Haiku for classification/light generation) via Claude Max subscription. For heavy-volume or lower-complexity agents in future, migrate to models via OpenRouter (GPT, Gemini, etc.) or Zen (open-source / SLM) to reserve Claude quota for the agents that need it most.
| Reports To | [CEO Agent / other agent] |
| Tools | [comma-separated tool list] |
| SKILL.md Context | [what domain knowledge the agent needs on every heartbeat] |
```

### Instruction Bundle Pattern

Each Paperclip agent gets a set of files loaded on every heartbeat wake:

| File | Purpose | Question Answered |
|------|---------|-------------------|
| `AGENTS.md` | Operating manual — responsibilities, delegation, safety rules | "What's my job?" |
| `SOUL.md` | Persona — strategic posture, voice, philosophy | "How should I think and speak?" |
| `HEARTBEAT.md` | Per-heartbeat checklist — concrete steps | "What do I do right now, in order?" |
| `TOOLS.md` | Notes on tools, APIs, skills | "What's in my toolbox?" |

### Project-Level Agent Context Files (DOX + CLAUDE.md)

For the codebase that the Paperclip company's agents work in, use the DOX framework (`agent0ai/dox`) for structured agent documentation:

| File | Format | Purpose |
|------|--------|---------|
| `AGENTS.md` (root) | DOX (agent0ai/dox) | Project-wide contract: identity, tech stack, agent roster, conventions. Agent-driven self-documenting hierarchy — agents create/update child AGENTS.md files as the project evolves. |
| `CLAUDE.md` (root) | Claude Code format | Commands, architecture rules, key file references. Supports `claude` CLI and Claude Code workflows. Lightweight supplement to the DOX AGENTS.md. |

**DOX workflow:**
1. Before any edit, the agent **walks the docs tree** from root to the target area
2. After meaningful changes, the agent **updates the affected AGENTS.md files**
3. Child AGENTS.md files provide local guidelines for specific subdirectories
4. The root AGENTS.md contains a project structure index and links to children

**Relationship between DOX AGENTS.md and Paperclip SKILL.md:**
- **AGENTS.md** (DOX) — project-level context for coding agents. Used when the agent modifies code, creates templates, or works in the codebase.
- **SKILL.md** (Paperclip) — business-level context for Paperclip heartbeat agents. Used when the agent performs its domain-specific responsibilities (email triage, financial analysis, etc.).
- Both are loaded into context on their respective wake cycles.
- The DOX AGENTS.md references the Paperclip company model (agents, hierarchy, stack). The Paperclip SKILL.md references the codebase conventions where appropriate.

### Goal Hierarchy Pattern

```
Mission: [company mission]

  ├── Project Goal: [major workstream]
  │   ├── Agent Goal (Agent Name): [measurable outcome]
  │   └── Agent Goal (Agent Name): [measurable outcome]
  │
  ├── Project Goal: ...
  │
  └── Project Goal: Run a healthy company
      ├── Agent Goal (CEO Agent): Propose strategy adjustments weekly
      ├── Agent Goal (Founding Engineer): Keep infrastructure at 99.9% uptime
      └── Agent Goal (Chief of Staff): Monitor company health and route escalations
```

Every Paperclip ticket must trace back to a goal. If a task can't be traced, it doesn't get worked on.

### Budget Enforcement

| Setting | Purpose |
|---------|---------|
| Company-wide cap | Hard stop on total monthly spend |
| Per-agent cap | Prevents one runaway agent from eating everyone's budget |
| Heartbeat interval | Frequency control — longer intervals = fewer runs = less cost |
| Manual mode | `heartbeat.enabled: false` — trigger on-demand only |
| warnPercent (default 80) | Soft warning before hard stop |
| hardStopEnabled (default true) | Agent auto-paused at 100% |

Set budgets via Paperclip API:

```bash
# Company-wide cap
curl -X PATCH "$PAPERCLIP_API_URL/api/companies/$COMPANY_ID/budgets" \
  -H "Authorization: Bearer $PAPERCLIP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "budgetMonthlyCents": 10000 }'

# Per-agent cap
curl -X PATCH "$PAPERCLIP_API_URL/api/agents/$AGENT_ID/budgets" \
  -H "Authorization: Bearer $PAPERCLIP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "budgetMonthlyCents": 2500 }'
```

### Governance Table

| Action | Authority | Routing |
|---|---|---|
| Hire new agent | Board approves | CEO proposes → Chief of Staff routes → Board decides |
| Budget overrides | Board approves | Agent paused → CEO escalates → Chief of Staff routes → Board |
| Strategy changes | Board decides | CEO proposes → Chief of Staff reviews → Board approves |
| Agent pause/terminate | Board executes | CEO recommends → Chief of Staff routes → Board acts |
| Credentials (API keys, access grants, payment cards) | Board provides via Telegram DM | Chief of Staff requests → Board sends securely → Chief of Staff stores in Paperclip secrets |
| Weekly company health check | Chief of Staff reports | Paperclip API query → formatted Telegram brief to Board |

### Chief of Staff Operational Boundary

The Chief of Staff (Hermes) follows a strict boundary for when to act directly vs. route through Paperclip:

| Do Directly (the user asked you) | Route Through Paperclip (company tasks) |
|---|---|
| Landing page copy changes | Clerk, Stripe, dashboard, email templates |
| Pricing updates | Any infra or code change |
| Config/credential file reads | Content/design production |
| Answering questions | Market research reports |
| Small direct fixes the user requested | Client work, onboarding, support |
| Archiving/cleanup tasks | Hiring new agents |

**Golden rule:** If a task involves modifying code, creating content, setting up a service, or doing work that an agent was hired to do — route it through Paperclip. Only execute directly when the user explicitly asks you to do something by name.

### CEO Escalation Chain (Built into CEO Agent HEARTBEAT.md)

The CEO Agent monitors for these escalation triggers every heartbeat:

| Trigger | What Happens |
|---|---|
| **Blocked > 1 heartbeat cycle** | CEO cannot unblock → marks issue `blocked` → Chief of Staff polls and triages |
| **Agent error or failure** | Heartbeat failed/crashed → CEO creates blocked issue → Chief of Staff either tells CEO how to fix or routes to Board |
| **Needs human input** | Credentials, approval, decision → CEO marks issue `blocked` with clear "what's needed" field → Chief of Staff presents to Board |
| **Budget incident** | Agent hit 80%+ spend or hard stop → CEO reviews → Chief of Staff routes budget override to Board |
| **Production outage** | Any service down → CEO sets priority `critical` → Chief of Staff alerted immediately |
| **Unexpected finding** | Competitor launch, regulatory change, security issue → CEO creates issue → Chief of Staff routes to Board |

**Chief of Staff response to escalations:**
1. Poll blocked issues via `GET /api/companies/{id}/issues?status=blocked` periodically
2. For each: either tell the CEO how to fix it, or route to the Board for a decision
3. Update the issue with guidance → CEO applies it and unblocks

### Daily Status Report Pattern

The CEO Agent produces a structured daily status report every morning heartbeat and posts it as a comment on a dedicated archive issue.

**Report format:**
```
## Daily Status — YYYY-MM-DD

### Active Work
- Issue | Status | Summary | ETA

### Blockers / Escalations
- Issue | What's blocked | Why | Needs

### Agent Health
- Each agent: last heartbeat, any errors, status

### Revenue / Pipeline
- Pipeline count, warm conversations, inbound signals

### Key Decisions Needed
- Items requiring Board or Chief of Staff input
```

**Cron setup (Hermes Chief of Staff side):**
- Create a cron job that runs 9:30 AM ET weekdays
- It checks the daily status archive issue for today's report
- If found, forwards to the Board. If not found, wakes the CEO agent on-demand.

### Acceptance Criteria: GitHub Submission Before Review

**All work deliverables MUST be committed and pushed to `origin/main` before marking an issue `done` or `in_review`.** This is a company-wide governance rule enforced by the CEO Agent.

Checklist before marking any issue complete:
1. `git add <files>` — stage all new/changed files
2. `git commit -m "descriptive message"` — commit with a clear message referencing the issue number
3. `git pull origin main --rebase` — sync with remote
4. `git push origin main` — push to GitHub

If push fails due to divergence, handle the rebase before retrying. This applies to all agents — the CEO enforces it on delegated work too.

### Hiring New Specialist Agents (On-Demand Pattern)

When a new specialist role is needed (designer, marketing, data analyst, etc.), the CEO Agent handles the hire:

1. **Create the Paperclip agent via API** — `POST /api/companies/{id}/agents`
2. **Set agent config:**
   - `heartbeat.enabled: false` (on-demand only)
   - `adapterType: claude_local` (or appropriate)
   - `reportsTo: <CEO agent ID>`
   - `budgetMonthlyCents: 1000-1500` ($10-15/mo for light roles)
3. **Write instruction bundle** — 4 files:
   - `AGENTS.md` — role description, domain responsibilities, reporting line, tools available
   - `HEARTBEAT.md` — on-demand only, check assigned issues on wake, produce real deliverables on disk, comment on issue with file paths, mark done/blocked/in_review
   - `SOUL.md` — persona: design philosophy, voice, aesthetic sensibility for the specific domain
   - `TOOLS.md` — actual tools available (file system, image generation, browser, etc.)
4. **Assign first task** — create issue with `assigneeAgentId` set to the new agent; they auto-wake
5. **Budget note:** On-demand agents consume Claude credits only when they work. For one-off tasks, on-demand is more cost-effective than a recurring schedule.

### Guide Delivery as File Attachments

When the Board requests a guide or document (deployment guide, setup guide, compliance doc), send it as a **file attachment** using the platform's file delivery convention (e.g. `MEDIA:/path/to/file.md` on Telegram).

## Data Backup & Recovery

Paperclip generates automatic PostgreSQL dumps every hour at `~/.paperclip/instances/default/data/backups/` (`.sql.gz`, ~24 MB). These cover the database only. For a complete off-machine backup, also capture `companies/`, `projects/`, `workspaces/`, `secrets/`, and `data/storage/` — see `references/backup-and-recovery.md`.

**Gateway reboot detection:** Use `scripts/gateway-reboot-notice.sh` as a `no_agent=true` cron job every 2 minutes. It detects gateway restarts via cron ticker heartbeat timestamp gaps (>3 min = reboot). Silent when healthy, outputs post-reboot status on restart. Dedup: one notification per 10 minutes. Heartbeat timestamps may contain fractional seconds — use `cut -d. -f1` to parse.

### Build Sprint Execution Pattern

The Chief of Staff (Hermes) acts as the human's daily interface to the Paperclip company. The human never opens the Paperclip UI for routine operations. Interaction pattern:

| Human Says | Chief of Staff Does |
|---|---|
| "How's the company doing?" | `GET /api/companies/{id}` + agent list → formatted status report |
| "Approve the CEO's budget override" | `POST /api/companies/{id}/budget-incidents/{id}/resolve` → confirm |
| "Need to set up a Stripe API key" | Capture credential → store in Paperclip secrets → confirm |
| "What's our spend this month?" | `GET /api/companies/{id}/budgets/overview` → formatted table |
| "Pause the Communications Agent" | `PATCH /api/agents/{id}` with `status: "paused"` → confirm |
| "Create a new task" | Capture details + target agent → `POST /api/companies/{id}/issues` |
| "What's the CEO's latest run?" | `GET /api/agents/{id}/runs` → run transcript summary |

The Chief of Staff does NOT route everything to the human. Routine operational items (agent heartbeat status, completed tasks, schedule checks) are handled directly. Only board-level items (budget overrides, hires, strategy shifts, legal/compliance, new credentials) reach the human.

## Paperclip ↔ Hermes API Integration

Base URL: `http://localhost:3100/api`

| Check | Endpoint | Response |
|---|---|---|
| Server health | `GET /api/health` | `{status: "ok", ...}` |
| Company overview | `GET /api/companies/{id}` | budget, spend, status |
| Agent list | `GET /api/companies/{id}/agents` | all agents with status |
| Agent detail | `GET /api/agents/{id}?companyId={id}` | config, chain of command, access |
| Budget overview | `GET /api/companies/{id}/budgets/overview` | policies, incidents, pauses |
| Create issue/task | `POST /api/companies/{id}/issues` | issue object |
| Trigger heartbeat | `POST /api/agents/{id}/heartbeats` | run result |
| Update agent | `PATCH /api/agents/{id}` | pause, resume, reconfigure |

### Agent Auto-Wake Behavior

Agents auto-wake when issues are assigned to them IF their runtime config has `wakeOnDemand: true` and `maxConcurrentRuns > 0`. No manual heartbeat POST is needed — creating the issue and setting the assignee triggers the agent automatically. This is the default for CEO agents.

For agents with `heartbeat.enabled: true`, they also run on their interval schedule and pick up assigned issues during those cycles. The wakeOnDemand setting controls whether they wake on issue assignment outside of scheduled heartbeats.

**Chief of Staff workflow:** Create issues normally via `POST /api/companies/{id}/issues` with `assigneeAgentId` set. The agent wakes itself. Check the agent's `status` field to confirm it went from `idle` → `running`.

### Agent Wake Behavior

Agents auto-wake when issues are assigned to them IF their runtime config has both `wakeOnDemand: true` and `maxConcurrentRuns > 0`. No manual heartbeat POST is needed — creating the issue and setting the assignee triggers the agent automatically. This is the default for CEO agents. For agents with `heartbeat.enabled: true`, they also run on their interval schedule and pick up assigned issues during those cycles.

Chief of Staff workflow (from Telegram/Discord/etc.):
1. "How's the company?" → `GET /api/companies/{id}` + agents list → formatted report
2. "Approve the budget override" → `POST /api/companies/{id}/budget-incidents/{id}/resolve` → confirm
3. "Pause Agent X" → `PATCH /api/agents/{id}` with `status: "paused"` → confirm
4. "What's our spend?" → `GET /api/companies/{id}/budgets/overview` → formatted table
5. "Create a task for an agent" → `POST /api/companies/{id}/issues` with `assigneeAgentId: "<agent-id>"` → agent auto-wakes

## Pitfalls

- **Don't make the human the CEO in Paperclip.** The human should be Board. The CEO should be a Paperclip agent. If the human is CEO, escalations don't route properly and the human ends up operating instead of governing.
- **Don't skip the Chief of Staff layer.** Without a Chief of Staff, every Paperclip notification reaches the human directly, defeating the async model. The Chief of Staff curates.
- **Don't give specialist agents direct escalation to the human.** All escalations go CEO → Chief of Staff → Board. This prevents interruption overload.
- **Don't enable heartbeats before the workflow is validated manually.** Run Layer 1 (communication) by hand for 2-4 weeks before turning on automation. Each layer must prove value before becoming autonomous.
- **Don't use Hermes `delegate_task` when a Paperclip company exists.** When a Paperclip company is running, route all task delegation through the Paperclip API: create issues via `POST /api/companies/{id}/issues` with the target agent as `assigneeAgentId`, then wake the CEO agent on-demand. Paperclip agents already have instruction bundles, budgets, and audit trails — Hermes `delegate_task` spawns ephemeral subagents with none of these. The human will notice and correct you. The Paperclip CEO agent auto-wakes when issues are assigned (`wakeOnDemand: true` with `maxConcurrentRuns > 0`) — no manual heartbeat trigger is needed.
- **Don't skip SKILL.md files.** Agents without instruction bundles make poor decisions. The 4-file pattern (AGENTS.md, SOUL.md, HEARTBEAT.md, TOOLS.md) is the minimum viable configuration.
- **Don't fight SaaS signup captchas.** When setting up startup stack accounts (Supabase, Clerk, Resend, etc.), automated browser signups hit hCaptcha/reCAPTCHA and will fail. Identify this constraint upfront — present the human with a clear one-click list of 5-6 services to sign up via GitHub OAuth (they're already logged into GitHub), and ask them to send back API keys. This takes ~12 minutes of their time vs. many turns of failed automation.
- **Supabase direct DB connections are often IPv6-only.** Many VPS/hosted environments lack IPv6. You cannot connect via `psql` or `psycopg2` directly. Use the Supabase Management API SQL endpoint (needs a Personal Access Token `sbp_...`) or ask the human to paste SQL into the Supabase Dashboard SQL Editor. The connection pooler also requires correct `project-ref` in the hostname. **Important caveat:** the Management API SQL endpoint strips single quotes from queries — use PostgreSQL dollar-quoting (`$$text$$`) for all string literals. See the dedicated [Supabase Schema via Management API](./references/supabase-schema-via-mgmt-api.md) reference for the exact API calls and workaround.
- **Cloudflare DNS is configurable via REST API.** Once the human provides an API token, use `POST https://api.cloudflare.com/client/v4/zones/{zoneId}/dns_records`. CNAME the apex to the Fly.io app hostname with `"proxied": true`. Minimal setup: apex + www records.
- **Secrets flow: human provides → Chief of Staff stores immediately.** API keys arrive via secured DM (Telegram). Chief of Staff calls `POST /api/companies/{id}/secrets` and stores them in Paperclip's encrypted secret store. Keys never appear in conversation history, SKILL.md files, or GitHub. Agents reference secrets by name at runtime.
When the Board requests a guide or document (deployment guide, setup guide, compliance doc), send it as a **file attachment** using the platform's file delivery convention (e.g. `MEDIA:/path/to/file.md` on Telegram).

## Data Backup & Recovery

Paperclip generates automatic PostgreSQL dumps every hour at `~/.paperclip/instances/default/data/backups/` (`.sql.gz`, ~24 MB). These cover the database only. For a complete off-machine backup, also capture `companies/`, `projects/`, `workspaces/`, `secrets/`, and `data/storage/` — see `references/backup-and-recovery.md`.

**Gateway reboot detection:** Use `scripts/gateway-reboot-notice.sh` as a `no_agent=true` cron job every 2 minutes. It detects gateway restarts via cron ticker heartbeat timestamp gaps (>3 min = reboot). Silent when healthy, outputs post-reboot status on restart. Dedup: one notification per 10 minutes. Heartbeat timestamps may contain fractional seconds — use `cut -d. -f1` to parse.

### Build Sprint Execution Pattern

When the CEO or Chief of Staff is asked to execute a phase (not just plan one), use this operational sprint pattern to coordinate multiple workstreams in parallel.

### Sprint Kickoff

1. **Read the phase document** — extract all tasks from the Build Tasks, Agent Tasks, and Board Tasks tables
2. **Decompose into parallel workstreams** — group tasks by owner (CEO/Founding Engineer/Comms/etc.) and identify which ones you can execute vs. need human input
3. **Set up a todo list** — use the todo tool with one item per workstream, ordered by priority. Mark completion as each workstream finishes.

### Workstream Decomposition Table

| Column | Meaning |
|--------|---------|
| **Owner** | Who does this work |
| **Can I execute?** | Yes = fully autonomous; No = blocked (needs credential, human registration, approval) |
| **Autonomous path** | What I can do without the human (write the spec, create the guide, prepare the template) |
| **Human blocker** | Exactly what the human needs to do and why |
| **Fallback deliverable** | If blocked, produce a detailed setup guide instead of stopping |

Categorize every task:
- **✅ Autonomous** — files, code, templates, docs, config changes
- **⏳ Needs human** — SaaS account registration (reCAPTCHA), domain DNS changes, payment details, OAuth tokens
- **❌ Needs approval** — strategy decisions, pricing changes, budget overrides

### Human-Blocker Detection Pattern

Many SaaS signup flows (Clerk, Stripe, Supabase, Sentry, Datadog, etc.) use reCAPTCHA or bot detection that browser automation cannot bypass without residential proxies. **Detect this early — don't fight the form.**

```
Attempt signup (1 try) →
  └── Success? → Store keys in .env.production → done
  └── reCAPTCHA/bot block or needs company email? →
       └── Create detailed setup guide → note as ⏳ in status report
```

The fallback deliverable for a blocked SaaS task is always a **step-by-step setup guide** saved to the plan directory. The guide should include:
- Exact registration URL
- Free tier details verified from the pricing page
- Which API keys to copy
- Which products/events to create (for Stripe: pricing tiers, coupons, webhook events)
- Confirmation that the stored credential location is ready (`.env.production`)

### Setup Guide Template

When a service registration is blocked, produce a markdown guide at the project's `plan/` directory:

```markdown
# <Service> Setup Guide

## Prerequisites
- What the human needs (company email, EIN, business address, etc.)

## Step-by-Step
1. Go to <URL>
2. Click "Sign up" — use GitHub OAuth if available (fastest)
3. Choose <Free Plan Name> — no credit card needed
4. Verify email

### Configure Application
1. Create application named "<Name>"
2. Enable <features>
3. Navigate to API Keys section

### Get Credentials
- `KEY_1` — from <location in dashboard>
- `KEY_2` — from <location in dashboard>

### Create Resources
| Resource | Name | Price | Metadata |
|---|---|---|---|
| Product 1 | Starter | $1,200/mo | tier=starter |

### Webhook
- Endpoint: `https://<domain>/api/webhooks/<service>`
- Events to subscribe: <event list>

### Store Keys
Add to `.env.production`:
```env
SERVICE_KEY_1=...
SERVICE_KEY_2=...
```
```

### Status Report Format

After executing or attempting all workstreams, deliver a status report covering the full sprint.

**Structure:**

```markdown
# Phase N Build Sprint — Status Report

**From:** <Agent Name, Title>
**To:** Chief of Staff / Board
**Date:** <date>

## Executive Summary

<One paragraph: what's done, what's blocked, what needs human input>

---

## Task Results

### ✅ Task N: <Name> — DONE
- **Deliverable:** <file path>
- <Key detail about what was produced>

### ⏳ Task N: <Name> — NEEDS HUMAN
- **Guide created:** <file path>
- **Free tier verified:** <plan details>
- **Why blocked:** <specific blocker>
- **Action needed:** <exact steps for human>

---

## Files Created/Modified

| File | Change |
|------|--------|
| `path/to/file.md` | **Created** — <what it is> |
| `path/to/script.py` | **Patched** — <description> |

---

## What Needs Board Input

1. <Item requiring approval or action>
2. <Next item>
```

### Per-Workstream Handoff

When you complete a workstream that someone else (human or agent) needs to pick up:
- Save any prepared files with clear intent in the filename
- Note in the status report exactly what remains and who owns it
- Use the todo tool to track lifecycle (all workstreams → completed or with clear next-owner)

### Sprint Execution Pitfalls

- **Don't attempt the same SaaS signup more than once.** If the first attempt hits reCAPTCHA/bot detection, move immediately to guide-generation. Retrying wastes turns and never succeeds.
- **Don't store keys in code even temporarily.** Write to `.env.production` from the start. Verify `.gitignore` already matches `*.env`.
- **Don't mix autonomous and blocked tasks in the same report section.** Separate them clearly with ✅ and ⏳ markers so the human can scan quickly.
- **Don't forget the Board's decision items.** The open questions/approvals box is the most important section — the human reads this first.
- **Don't assume you can create accounts on behalf of the business.** Company email access, EIN, and business address are almost always required for Stripe and similar financial services. Plan for this.

## Verification

After creating a Paperclip company and agents:

1. `curl http://localhost:3100/api/health` — server is up
2. Open Paperclip UI at `http://localhost:3100` — company and agents visible
3. Check agent status is `idle` (not `error` or `pending_approval` if board created directly)
4. Trigger one manual heartbeat per agent and verify the run completes cleanly
5. Check budget overview: all agents have caps set, no incidents pending
6. Chief of Staff: test one API query from Telegram to confirm connectivity

## See Also

- `paperclip-company` skill — Paperclip company setup, governance, and phased execution planning
- `efficient-operation` skill — token-efficient operations and platform interaction principles
- `references/phased-execution-plan-template.md` — reusable phase document template
- `references/agency-intelligence-hierarchy-example.md` — complete worked example from this pattern
- `references/supabase-schema-via-mgmt-api.md` — running DDL via Supabase Management API when direct DB connections fail (IPv6, dollar-quoting workaround)
- `references/supabase-keepalive.md` — preventing free-tier Supabase project pause with periodic lightweight pings (REST API, Management SQL, or direct psql); includes Hermes cron script template and Paperclip task routing patterns
- `references/agentic-gtm-playbook.md` — zero-capital, DesignJoy-inspired customer acquisition strategy for agent-run companies with no founder sales involvement. Covers organic pipeline channels (Reddit, X/Twitter built-in-public, LinkedIn), waitlist-gated rollout, risk-reversal offer design, and sending domain infrastructure.
- `references/local-instance-lifecycle.md` — local Paperclip instance lifecycle: startup, health check, watchdog pattern, and cron scheduler restart behavior. Includes the deterministic `scripts/paperclip-watchdog.sh` (no_agent=true watchdog script for auto-restart on gateway restart or crash).
- `scripts/paperclip-watchdog.sh` — deterministic health check + auto-restart script. Silent when healthy, only outputs when action is taken. Designed for no_agent=true cron jobs running every 2-5 minutes.
- `scripts/gateway-reboot-notice.sh` — gateway reboot detection via heartbeat timestamp gaps (no_agent cron, every 2m). Silent when healthy.
- `references/backup-and-recovery.md` — Paperclip data layout, internal hourly DB dumps, external GitHub backup pattern
- `references/stripe-webhook-api-setup.md` — creating Stripe webhook endpoints via API
