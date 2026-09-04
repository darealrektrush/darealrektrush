# Automation Opportunity Intelligence Engine — Planning Docs

Architecture and MVP planning for an internal B2B AI-automation **prospecting and
opportunity-discovery** platform. Per the brief, **no application code is built yet** —
this set defines the architecture and MVP boundary first.

**Core pipeline:** `DISCOVER → ENRICH → ANALYZE → IDENTIFY PAIN → DESIGN AUTOMATION →
SCORE → PROSPECT`

**Product principle:** identify **business problems first, technology second**; sell
**outcomes**, not bots. Every fact is labeled `OBSERVED / INFERRED / UNKNOWN` with source
and timestamp; nothing is fabricated.

## Read in order

| # | Deliverable | Doc |
|---|-------------|-----|
| 0 | Overview, principles, recommended stack | [00-overview.md](00-overview.md) |
| 1 | Architecture proposal | [01-architecture.md](01-architecture.md) |
| 2 | Database schema | [02-database-schema.md](02-database-schema.md) |
| 3 | Data-source strategy | [03-data-sources.md](03-data-sources.md) |
| 4 | Opportunity-scoring model | [04-scoring-model.md](04-scoring-model.md) |
| 5 | MVP implementation plan | [05-mvp-plan.md](05-mvp-plan.md) |
| 6 | Recommended repository structure | [06-repo-structure.md](06-repo-structure.md) |
| 7 | Security / compliance | [07-security-compliance.md](07-security-compliance.md) |
| 8 | Estimated API / service costs | [08-costs.md](08-costs.md) |

## TL;DR

- **Stack:** Supabase Postgres in a **dedicated new org** + `pgvector` ·
  Next.js dashboard on Vercel · long-running crawl/LLM workers on Render · `pg-boss` queue
  on Postgres for MVP · Claude Haiku (extraction) + Sonnet (design/outreach).
- **MVP:** full pipeline for **one vertical — home-service / contractors** in one metro,
  through a working dashboard with a detailed prospect report and an evidence-grounded
  outreach angle.
- **Modularity:** every external source/LLM sits behind a provider interface; verticals
  and signal codes are seed **data**, so new sources and verticals are added without a
  core rewrite.
- **Cost:** ~$85–$205/mo at 1,000 prospects/mo (~$0.09–$0.21 per processed prospect),
  dominated by discovery + LLM; see [08](08-costs.md).

## Status & next step

Planning complete. **Do not begin major implementation until these boundaries are
approved.** On approval, Phase 0 in [05-mvp-plan.md](05-mvp-plan.md) (Supabase project +
schema + monorepo scaffold) is the first build step.
