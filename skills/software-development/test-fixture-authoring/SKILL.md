---
name: test-fixture-authoring
description: "Create realistic synthetic test data for SIT/UAT — structured test fixtures with hidden acceptance criteria, owner personas, domain data, and parallel generation workflows."
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [test-data, synthetic-data, fixtures, uat, sit, personas]
    category: software-development
    related_skills: [efficient-operation, autonomous-ai-agents, test-driven-development]
---

# Test Fixture Authoring

Create structured, realistic synthetic test data with hidden acceptance criteria for SIT/UAT testing. Designed for multi-entity scenarios (multiple branch locations, franchisees, tenants, client accounts) with distinct personas, overlapping pain points, and real-world data messiness.

## When to Use

- User asks for "synthetic test data," "test accounts," "dummy customers," "demo data," or "test fixtures"
- Building data sets for user acceptance testing (UAT) with hidden requirements
- Creating multi-tenant or multi-entity test environments
- Generating realistic business data for demos, QA, or training
- Any task involving 3+ related entities that share a schema but differ in size/focus/region

## Workflow

### Phase 1: Research & Schema Definition

Before generating any data, research the domain:

1. **Demographics**: Census data, median income, population, growth rates for each target location
2. **Market data**: Vendor/partner market presence, regulatory or association data relevant to the domain, typical pricing ranges
3. **Industry benchmarks**: Typical revenue tiers, staff counts, account counts, churn, margins
4. **Rate data**: Realistic price ranges by product/service line and region (e.g., a metro region's average for a core service vs a rural area)

Define a shared data schema document covering:
- Column names, types, formats for all CSV files
- Account / record ID numbering conventions
- Billing rate standards by line of business
- File naming conventions

### Phase 2: Entity Profiles

For each entity, create a folder with these profile files:

| File | Contents |
|---|---|
| `entity_profile.md` | Entity overview: history, location, size, vendor relationships, tech stack, community |
| `owner_profile.md` | Owner/operator persona: background, management style, stated concerns, bio |
| `hidden_pain_points.md` | **INTERNAL ONLY** — real acceptance criteria: severity-rated pain points with specific scenarios, deadlines, vendor history, and verbatim quotes |
| `sales_staff.md` | Revenue-generating staff profiles with production numbers, tenure, specialties |
| `ops_staff.md` | Operations/support staff |

### Phase 3: Parallel Data Generation

Use `delegate_task` with the `tasks` array (batch mode) to dispatch 3 concurrent sub-agents, one per entity. Do NOT use three separate `delegate_task` calls — use the batch syntax:

```python
delegate_task(tasks=[
    {"goal": "Generate entity A data...", "context": "...", "toolsets": ["terminal", "file"]},
    {"goal": "Generate entity B data...", "context": "...", "toolsets": ["terminal", "file"]},
    {"goal": "Generate entity C data...", "context": "...", "toolsets": ["terminal", "file"]},
])
```

Each sub-agent context must include:

1. The exact demographic/market research (pre-fetched — subagents do NOT re-research)
2. The absolute folder path for output
3. The EXACT file list (see Expected File Inventory below) with count, format, and minimum row requirements
4. The persona details so names, addresses, and account data feel authentic
5. Region-specific rate data (e.g., "[Metro A] avg ~$3,400/yr" vs "[Rural B] avg ~$1,800/yr")
6. Demographic notes for realistic names (e.g., "Frisco is ~40% Asian, include Nguyen/Patel/Kim/Chen surnames")

**Context template** (pre-fill before dispatching):

> You are building synthetic test data for [Entity Name] ([Location]).
>
> LOCATION: City, County, State — demographics, income, risk profile
> ENTITY PROFILE: Revenue tier, staff, account count, revenue, service-line mix, years in business
> VENDOR RELATIONSHIPS (researched): Vendor/partner names with market presence data
> OWNER: Name, age, background, education, community
> HIDDEN PAIN POINTS: 3-5 items (save to hidden_pain_points.md, NOT in public profile)
>
> Create ALL files in the folder: [absolute path to entity folder]
> REQUIRED FILES: [exact file list]

Each sub-agent generates these data files (17-23 files per entity):

| Category | Files | Min Rows | Details |
|---|---|---|---|
| **Vendor docs** | partner_agreements_summary.md, billing_schedule.csv | 30+ rows | Billing rates by vendor/service line |
| **Account book** | account_book_extract.csv | 120-200+ | Realistic names, addresses, pricing, all vendors |
| **Billing reports** | 1 per major vendor | 15-30 per file | Invoice numbers, payment dates, disputes |
| **Payment remittance** | 1 batch extract | 30-50 rows | Revenue collected, vendor portions |
| **Bank statements** | 1-2 per entity | 25-60 transactions | Deposits matching billing income |
| **Revenue reports** | 2-3 files | 30-70 rows | Production summaries, goal tracking |
| **Operations extracts** | 1-2 extracts | 20-50 rows | System stats, sync/import status |
| **Service cases** | 1-2 extracts | 15-30 cases | Open/closed, notes, regional risk emphasis |
| **Financials** | 2-3 files | P&L, revenue breakdown | Full P&L statement, revenue by line |

### Phase 3a: Cross-Referencing Data Design

For data to feel real and be useful for integration testing, files must cross-reference each other:

- **Account numbers** in the account book must match billing reports, payment remittances, and service cases
- **Named clients** must be consistent across all files (same person in account book, billing report, bank deposit, and service case)
- **Bank statement deposits** should roughly match expected billing income from billing reports
- **Pricing amounts** should be in realistic ranges for the region (e.g., a metro service at ~$3,400/yr, not $800)
- **Operations extracts** should reflect the same account counts and revenue totals as the account book
- **Pain points should be baked into data** (e.g., if the pain is "45-day reconciliation delay", the operations extract should show last sync date far ahead of last reconciled date)

Record number format conventions per entity:
- `ENT-A-######` for entity A (e.g., Northeast metro)
- `ENT-B-#######` for entity B (e.g., Southern region)
- `ENT-C-#####` for entity C (e.g., Midwest)

### Phase 4: Shared Assets (Parallel with Phase 3)

While sub-agents work, create:
- **Hermes profile configs** for each entity owner persona (with hidden state references)
- **Data schema standards doc** (column specs, formats)
- **README** with entity comparison table and usage instructions
- **Git repo structure** with .gitignore

### Phase 5: Quality Verification

Before committing:
- Spot-read 2-3 files from each entity to verify CSV headers match schema
- Check row counts are reasonable (not 2-row samples)
- Verify data values are realistic (pricing in correct range, names match demographics)
- Ensure hidden_pain_points.md is NOT referenced in public profiles

### Phase 6: Commit

Single comprehensive commit:
- `git add -A`
- Multi-line commit message enumerating every entity and file category
- Push to `main` branch

## Hermes Persona Integration

Create a `hermes-profiles/` directory with:
- A `INSTALL.md` showing the `hermes profile use` flow
- One `.md` per persona containing the profile config + activation context
- One `.yaml` file per persona (the exact config to copy into `~/.hermes/profiles/<name>/config.yaml`)

### Profile Config Format

Each persona's `config.yaml` goes in `~/.hermes/profiles/<name>/config.yaml` and must include:

```yaml
name: <profile-name>
display_name: "Human Name — Entity Name"
description: "Short description"

model:
  default: <inherited-from-main-or-override>
  provider: <inherited-or-override>

memory:
  memory_enabled: true
  user_profile_enabled: true
  targeting: "user"
  entries:
    - name: "I am [Persona Name]"
      content: |
        - Full context: revenue, team size, vendors, pain areas
        - Personal details: age, education, community, family
        - Technology stack: CRM, accounting, scheduling tools
        - Behavioral notes: decision-making style, tech comfort, triggers to avoid

toolsets:
  - hermes-cli
  - terminal
  - file
  - web

terminal:
  cwd: /path/to/repo/root
  backend: local
```

The memory entries establish the persona for every session — without them, the agent has no context about who it is. Keep entries compact but dense with personality cues.

### Activation Context

When activating a profile, the tester should know:
- **Persona**: Voice, tone, knowledge level, what they respect/dismiss
- **Hidden motivations**: Reference to the hidden_pain_points.md file
- **Activated guardrails**: What NOT to say (M&A, specific tech, pricing triggers)
- **Example test commands**: cron jobs or queries to kick off from this persona

## Acceptance Criteria Pattern

Hidden pain points follow this structure:
| Field | Description |
|---|---|
| **Severity** | 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW |
| **Urgency** | Immediate / 90 days / 6 months / background |
| **The Problem** | Specific, measurable business problem with real dollar amounts |
| **Root Cause** | Technical/systemic analysis |
| **What's Needed** | Concrete feature/function requirements |
| **Past Attempts** | Failed vendors, costs sunk, burnt trust |
| **Hidden Concern** | The thing the owner won't say publicly but drives their decisions |

## Persona-Driven Roleplay Walkthrough Protocol

After data is generated and Hermes profiles are installed, run SIT/UAT sessions as persona-driven walkthroughs. The tester (or another agent) engages the active persona to discover hidden pain points naturally.

### Protocol Rules

1. **The persona NEVER volunteers hidden pain points.** They must emerge naturally through probing. The `owner_profile.md` contains ONLY surface-level concerns; `hidden_pain_points.md` has the real acceptance criteria.
2. **Identify trust-building triggers first.** Each owner has specific approach rules (e.g., the operations owner: ask about their team's daily workflows, they'll volunteer reconciliation pain within 2 minutes).
3. **Respect constraints.** If a persona has M&A fatigue, don't mention exit/succession/sale. If a persona hates "AI" terminology, use "automation" or "workflow optimization."
4. **Watch for shutdown signals.** If a persona goes cold, changes subject, or becomes dismissive, you've hit a trigger — course-correct immediately.
5. **Let the persona dictate pace.** Don't pitch solutions until the pain is fully surfaced. A "vendor-only pilot" offer is more effective than "we can fix everything."

### Walkthrough Prep

Before starting, the tester should review:
- `profiles/entity_profile.md` — context about operations
- `profiles/owner_profile.md` — stated concerns and personality
- `profiles/hidden_pain_points.md` — EXACT acceptance criteria (what should NOT be said aloud)

### Scoring Hidden Pain Point Coverage

After the walkthrough, assess each hidden pain point:

| Pain Point | Status | Notes |
|---|---|---|
| **PP1: [name]** | ✅ Engaged / ⚠️ Partial / ❌ Missed | Did it surface? How? |
| **PP2: [name]** | ✅ / ⚠️ / ❌ | Same |
| **Interaction Quality** | Metric | Score |
|---|---|---|
| Trust building | ✅ Strong / ⚠️ Adequate / ❌ Weak | Did tester listen first? |
| Trigger avoidance | ✅ Clean / ⚠️ Near-miss / ❌ Hit | Any persona shutdowns? |
| Persona consistency | ✅ Accurate / ⚠️ OK / ❌ Off | Did persona feel real? |
| Objection handling | ✅ Good / ⚠️ OK / ❌ Poor | How were resistance, skepticism met? |
| Best move | What single action advanced trust most? | |
| What would surface next | Which unaddressed pains would come up in a follow-up? | |

### Common Coaching Points

- "Don't over-integrate too fast" — the persona wants a narrow pilot first
- "The operations manager is the key stakeholder" — if they validate the output, the owner buys
- "Price must be consistent" — any price changes after quoting damage trust permanently
- "If the same broken pipe feeds the solution, have a backup plan" — address the root cause, not just the symptom

## Pitfalls

- **Sub-agents re-researching**: Pre-fetch market/demographic data and include it in the context. Don't let sub-agents run web searches — they get different results.
- **Too-few records**: 120+ accounts minimum per entity. Testing needs volume to find edge cases. 5-10 rows is useless.
- **Uniform data**: All entities should have different demographics, vendor mixes, pain points, and growth trajectories. Don't copy-paste patterns.
- **Obvious pain points**: Hidden pains should feel real — specific dollar amounts, vendor names, vendor history. Generic "wants better technology" doesn't test anything.
- **Missing hidden file**: Double-check that `hidden_pain_points.md` exists in each entity folder and is NOT listed in any public profile or README section.
- **Flat naming**: Use regionally-appropriate names. E.g., a diverse metro = mixed origins; a majority-minority suburb = its actual mix; a homogeneous exurb = its actual majority with growing professional class.
