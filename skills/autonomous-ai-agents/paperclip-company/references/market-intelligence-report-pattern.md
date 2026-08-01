# Market Intelligence Report Pattern

A proven output format for Communication Agents running AI-driven market discovery. Used by the Communication Agent — 3x daily scans producing structured intelligence with strategic angles, content drafts, and actionable signals.

## Agent Configuration

| Setting | Value |
|---------|-------|
| Agent Role | Communication Agent (Director of Client Communication) |
| Heartbeat | Every 1 hour (3 content-production scans per day: morning, afternoon, evening) |
| Model | Claude Sonnet 4 (reasoning for synthesis) |
| Budget | $15/mo |
| Reports to | CEO Agent |

## Scan Sources

- LinkedIn industry-specific groups, comments on industry-influencer posts
- Reddit: domain-specific subreddits, small business communities
- Twitter/X: industry hashtags, business owner accounts
- Trade publications: comment sections on relevant articles
- Industry forums: member discussions, user groups
- Competitor websites: positioning language analysis
- Partner/vendor materials: language used with the target audience
- Regulatory sources: relevant agency rulings, enforcement actions

## Report Output Structure

Each heartbeat produces a single markdown report structured as follows:

### Header
```
# <Company Name> — Signal Scan & Content Production
**Date:** <date> | **Heartbeat:** <time of day scan>
```

### Signal Summary

Each signal gets its own section with:
1. **Source** — where found (publication, URL, date)
2. **Summary** — what the signal is, in 2-4 sentences
3. **Strategic angle** — a `>` blockquote starting with `> Key strategic angle:` that translates the signal into a financial/operational takeaway for business owners

Example:
```
### N. Signal Title
*Source: Publication Name, Date*

<2-4 sentence summary of the news/signal>

> Key strategic angle: <business takeaway>.
```

### Ready-to-Publish LinkedIn Posts

3 posts per heartbeat (9 per day), labelled POST A/B/C per scan:
- 900-1,200 character range (LinkedIn optimal)
- Starts with a hook sentence
- Industry analysis + actionable insight
- 3 relevant hashtags at the end
- Includes `*#IndustryTag*` formatting

### Email Openers

3 email opener drafts per heartbeat, each with:
- Subject line (short, curiosity-driven)
- 3-5 paragraph body with personalized opener, data point, and call to action

### Forum Response Templates

3 forum response templates (for domain-specific subreddits), each keyed to a specific trigger scenario:
- Scenario description: "Use when: <trigger>"
- 4-6 paragraph response with neutral, helpful tone
- Data-backed claims with specific numbers

## Example Signals with Strategic Angles

| Signal Type | Sample Strategic Angle |
|---|---|
| Market changes | "Businesses that coasted on tailwinds now face a volume-or-die moment." |
| Compensation/cost data | "If your cost structure is still modeled at 3-5% annual increases, you're understating burn." |
| Regulatory changes | "Compliance infrastructure cost just went up. Concentration in any one segment is now a balance sheet risk." |
| Competitive threats | "Technology ROI analysis — which tools reduce operational time vs. just add cost — is the CFO's job now." |
| Staffing trends | "Most business P&Ls haven't priced in the comp reset." |
| Market softening | "This is when financial modeling discipline separates businesses that grow from those that shrink." |

## Output Storage

- Reports posted as comments on the agent's assigned heartbeat issue in Paperclip
- Key findings also logged to the `discovery_findings` table in Supabase (when available)
- 3x daily scans produce 9 LinkedIn posts, 9 email openers, 9 forum templates per day
