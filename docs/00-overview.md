# Automation Opportunity Intelligence Engine — Overview

> **Status:** Architecture & MVP planning. No application code has been built yet.
> This document set is deliverable #0 and indexes deliverables #1–#8 requested in the brief.
>
> **Guiding rule (from the brief):** *Do not begin major implementation until the
> architecture and MVP boundaries are clearly defined.* These documents define them.

## 1. What this is (and is not)

This is an **internal prospecting and opportunity-discovery platform** for a B2B AI
automation business. It is a decision-support tool for the sales/solutions team — not a
public product and not a scraper.

**It is:** a pipeline that discovers businesses, analyzes how they operate today,
identifies workflows that could realistically be automated, scores the commercial
opportunity, and produces actionable prospect intelligence with source evidence.

**It is not:** a bulk email scraper, a lead-list vendor, or a "spray and pray" outreach
tool. We identify **business problems first, technology solutions second**, and we sell
**business outcomes** (faster lead response, fewer missed leads, less admin, more booked
appointments, lower support load) — not "bots" or "AI".

## 2. The core pipeline

```
DISCOVER → ENRICH → ANALYZE → IDENTIFY PAIN → DESIGN AUTOMATION → SCORE → PROSPECT
```

Each stage is an independent, replaceable module coordinated by a job queue. A business
flows through the pipeline once, and can be re-run when evidence goes stale.

| Stage | Input | Output | Deliverable ref |
|-------|-------|--------|-----------------|
| Discover | Vertical + geo + filters | Candidate companies | §1 brief / [03](03-data-sources.md) |
| Enrich | Company + website URL | Firmographics, contacts, socials | [03](03-data-sources.md) |
| Analyze (website) | Website HTML/DOM | Workflow & CTA signals | [01](01-architecture.md) |
| Detect tech | Website + headers | Technology stack | [01](01-architecture.md) |
| Identify pain | Signals + reviews + jobs | Pain signals w/ evidence | [01](01-architecture.md) |
| Design automation | All signals | Concrete workflows | [04](04-scoring-model.md) |
| Score | All of the above | 5 scores + priority | [04](04-scoring-model.md) |
| Prospect | Everything | Profile, dashboard row, outreach | [05](05-mvp-plan.md) |

## 3. Non-negotiable product principles

1. **Problem before solution.** Every automation opportunity must trace back to an
   observed operational problem with evidence.
2. **Concrete, not generic.** Never output "use AI for customer service." Output a named
   workflow (trigger → steps → integrations → impact).
3. **Provenance always.** Every important claim stores its **source** and **timestamp**.
4. **Truth labeling.** Every fact is tagged `OBSERVED`, `INFERRED`, or `UNKNOWN`.
   Inferred information is never presented as confirmed fact.
5. **No fabrication.** Never invent contact details, technologies, pain points, or
   opportunities. If a source is unavailable, the field is `UNKNOWN`.
6. **Compliance by construction.** Respect robots.txt, API terms, rate limits, privacy
   and anti-spam law. See [07](07-security-compliance.md).

## 4. Deliverables index

| # | Deliverable | File |
|---|-------------|------|
| 1 | Architecture proposal | [01-architecture.md](01-architecture.md) |
| 2 | Database schema | [02-database-schema.md](02-database-schema.md) |
| 3 | Data-source strategy | [03-data-sources.md](03-data-sources.md) |
| 4 | Opportunity-scoring model | [04-scoring-model.md](04-scoring-model.md) |
| 5 | MVP implementation plan | [05-mvp-plan.md](05-mvp-plan.md) |
| 6 | Recommended repository structure | [06-repo-structure.md](06-repo-structure.md) |
| 7 | Security / compliance considerations | [07-security-compliance.md](07-security-compliance.md) |
| 8 | Estimated API / service costs | [08-costs.md](08-costs.md) |

## 5. MVP boundary (one line)

**Build the full pipeline end-to-end for ONE vertical — home-service / contractor
businesses in a chosen metro — through a working dashboard, then widen.** Full MVP
scope in [05-mvp-plan.md](05-mvp-plan.md).

## 6. Recommended stack (infrastructure-aware)

Chosen to reuse infrastructure already connected to this account:

- **Database:** Supabase Postgres (org *Project Q* already present) — RLS, Auth,
  `pgvector` for evidence/dedupe embeddings.
- **Dashboard + API:** Next.js (App Router) on **Vercel** (hobby team present).
- **Crawlers & workers:** long-running Playwright/crawl work on **Render** (worker
  service + cron) — serverless timeouts on Vercel make it a poor fit for crawling.
- **Job queue:** `pg-boss` on the Supabase Postgres for the MVP (one fewer moving
  part); graduate to Redis/BullMQ (Render Key-Value) when throughput demands it.
- **LLM:** Anthropic Claude — Haiku for cheap high-volume extraction/classification,
  Sonnet for opportunity design and outreach copy. See [08-costs.md](08-costs.md).

Rationale and alternatives are in [01-architecture.md](01-architecture.md) and
[06-repo-structure.md](06-repo-structure.md).
