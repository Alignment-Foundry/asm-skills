# Skill Generalization Workflow

Stripping industry-specific language from a Paperclip company skill to make it generic and general-purpose, without losing its structural value.

## When to Use

- An existing Paperclip skill was written with concrete examples from one industry (insurance, SaaS, healthcare, etc.)
- You need to publish or share it as a portable, domain-agnostic reference
- The skill's structure (org hierarchy, API commands, agent archetypes, governance model) is valuable but the examples limit its audience

## Scan Targets

A Paperclip skill has two layers that can carry industry-specific language:

### 1. Core Files

| File | What to Check |
|---|---|
| `SKILL.md` | Description in frontmatter, scan-source lists, example agent tasks, "Human Says" sample commands, example company names, pricing/sizing assumptions, revenue targets |

### 2. Reference Files

| File | Industry Hotspots |
|---|---|
| `references/agency-intelligence-hierarchy-example.md` | Company name, mission statement, document-processing descriptions (e.g. "carrier statements"), API integration examples (e.g. "QuickBooks"), SKILL.md file names, build sequence steps |
| `references/market-intelligence-report-pattern.md` | Scan sources (specific subreddits like `r/insuranceagent`, trade publications, carrier names), signal examples with industry-specific angles, forum template recipients |
| `references/agentic-gtm-playbook.md` | Sample product/offer descriptions, risk-reversal guarantee text, social proof examples, community channel names, trade publication names |

## Generalization Strategy by Content Type

| Original | Generic Replacement |
|---|---|
| Specific subreddit (`r/insuranceagent`) | `domain-specific subreddits` or remove from inline example |
| Industry-specific publication (`Insurance Journal`) | `trade publications in the niche` |
| Carrier/vendor name (`Travelers, Hartford, Chubb`) | `partner/vendor materials` |
| Industry role (`insurance agencies`) | `small businesses` or `businesses` |
| Specific API/product (`QuickBooks API key`) | `Stripe API key` (broadly recognized) or `[Service] API key` |
| Industry jargon (`carrier statements`) | `client documents` / `vendor statements` / `business statements` |
| Agency-vs-business conflation (`X agencies are already using this`) | `X businesses are already using this` |
| Specific company name (`Agency Intelligence`) | `Example Services` or `[Company Name]` |
| SKILL.md file names with industry (`insurance-finance-glossary`) | `domain-finance-glossary` |

## Workflow (by file type)

### Core SKILL.md (surgical changes)

Use `patch` for targeted replacements — one change per call. Replacements are cheaper than rewrites and less error-prone.

**Recommended order:**
1. Frontmatter description — change "a real" to "any real" (signals general-purpose intent)
2. Table strings — scan agent-task tables for embedded industry references
3. Source-type lists — replace "agency-owner groups" → "industry-specific groups", "carrier" → "partner/vendor"
4. Example dialogs — replace brand-specific API examples with broadly recognized ones (e.g. QuickBooks → Stripe)

### Reference files (structural rewrites)

Use `write_file` for entire rewrites. Reference files are typically short enough to hold in a single call, and full rewrites avoid stale remnants.

**Rewrite pattern:**
1. Keep: org structure, agent roles, heartbeat schedules, budget tables, governance tables, API endpoints
2. Replace: company name, mission statement, industry-specific document roles, API integration examples, SKILL.md file names, build sequence tool mentions
3. Verify: search for `insurance|carrier|QuickBooks|r/insurance` after each rewrite

## Verification

After all changes:

```bash
# Check for remaining industry-specific language in the skill directory
grep -rn "insurance\|carrier\|r/insurance\|QuickBooks\|PropertyCasualty\|Insurance Journal" skills/<category>/<name>/

# Run the Hermes validator
./scripts/validate-skills.py

```

## Pitfalls

- **Don't assume "agency" is always industry-specific.** In the Paperclip context, "agency" means "Paperclip agent company" — a valid term. Only replace "agency" when it refers to the client's business type (e.g. "X agencies are already using this").
- **Don't forget the asm-skills repo.** The Hermes profile's skill at `~/.hermes/profiles/*/skills/` and the asm-skills repo at `projects/asm-skills/skills/` are separate copies. After editing one, sync the other via `bash scripts/sync-skill.sh <category>/<name>`.
- **Don't use `skill_manage(action='create')` for in-repo skills** — it writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo edits.
- **Check both occurrences** of duplicated sections. SKILL.md sometimes has duplicate "Data Backup & Recovery" and "Guide Delivery" sections at the bottom — a pre-existing artifact from earlier merges. Patch both instances.
