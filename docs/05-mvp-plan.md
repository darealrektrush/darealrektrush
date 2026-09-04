# Deliverable 5 — MVP Implementation Plan

## 1. MVP boundary

**One vertical, full pipeline, real dashboard.**

- **Vertical:** `home_services` (contractors: roofing, plumbing, HVAC, electrical,
  landscaping).
- **Geo:** one or two metros to bound cost (e.g. a single state/metro).
- **End to end:** discover → enrich → analyze → signals → opportunities → score → store →
  dashboard → detail report → outreach angle.

Explicitly **out of scope for MVP:** other verticals, paid enrichment (BuiltWith/PDL),
Redis/BullMQ, multi-user assignment beyond a simple owner field, automated *sending* of
outreach (we generate drafts; humans send).

## 2. The ten MVP capabilities (from the brief) → build items

| # | Capability | MVP build |
|---|-----------|-----------|
| 1 | Discover businesses | `DiscoveryProvider=google_places`, one query form in dashboard |
| 2 | Capture websites & public info | Enrichment stage writes `companies`, `contacts`, `company_locations` |
| 3 | Analyze websites | Crawler (fetch→Playwright) + DOM signal extraction |
| 4 | Detect operational signals | Signal Extraction Engine (in-house rules) |
| 5 | Identify automation opportunities | LLM Analyzer (Claude Sonnet), grounded output |
| 6 | Score each company | Scoring Engine (deterministic, v1 weights) |
| 7 | Store prospects | Supabase schema from [02](02-database-schema.md) |
| 8 | Dashboard | Next.js list: search/filter/sort/save/reject/tag/pipeline |
| 9 | Detailed report | Prospect detail view with OBSERVED/INFERRED/UNKNOWN labels |
| 10 | Outreach angle | Outreach Generator (Claude), evidence-grounded |

## 3. Phased plan

### Phase 0 — Foundations (½–1 wk)
- **Create a dedicated Supabase organization** for this business (dashboard-only step —
  the Management API does not expose org creation). Then create the project inside it:
  `automation-opportunity-engine`, region `us-west-1`. This keeps billing, members, and
  blast radius fully separate from any existing project.
- Enable `pgvector`, apply the [02](02-database-schema.md) migration, set up RLS +
  `app_members`.
- Monorepo scaffold ([06](06-repo-structure.md)), CI, env/secrets, provider registry
  skeleton, `pg-boss` queue on the Supabase DB.
- Object-storage bucket (Supabase Storage) for page snapshots.

### Phase 1 — Discovery + Enrichment (1 wk)
- Google Places `DiscoveryProvider`; write `companies` + `discovery_queries`.
- Enrichment stage: Places details + own crawl of contact/about → `contacts`,
  `company_locations`, socials. Dedupe via `website_domain` + `dedupe_embedding`.
- Evidence rows for everything. **Milestone:** a query produces deduped companies with
  contacts and provenance.

### Phase 2 — Website analysis + Tech + Signals (1–1.5 wk)
- Crawler with robots.txt compliance, snapshotting, page cap; Playwright fallback.
- In-house Technology Detector (the brief's tech list).
- Signal Extraction: OPERATIONAL + PAIN codes from DOM/CTAs, review summaries, and
  careers-page job postings. **Milestone:** companies carry typed signals with evidence.

### Phase 3 — Opportunities + Scoring (1 wk)
- LLM Analyzer: distilled-signal prompt → `opportunities` (+ integrations), with the
  grounding check (every cited signal must exist).
- Scoring Engine: five scores + `breakdown`. **Milestone:** every company has scored
  opportunities.

### Phase 4 — Dashboard + Detail + Outreach (1.5 wk)
- Next.js dashboard: filters (industry, location, score, automation type, size, tech,
  complexity, value, confidence, pipeline status), sort, save/reject/tag/assign,
  pipeline stages.
- Detail view: the 11 sections from the brief, with truth labels and a **Source
  Evidence** panel.
- Outreach Generator drafts angle + message from evidence. **Milestone:** a reviewer can
  work a queue of scored prospects end to end.

### Phase 5 — Hardening (ongoing)
- Rate-limit budgets per provider, retries/backoff, staleness re-queue, cost dashboard,
  score calibration ([04](04-scoring-model.md) §6).

**Rough total:** ~6–7 focused weeks for a single builder to a usable internal MVP.

## 4. Acceptance criteria

- Running one discovery query for roofing in the target metro yields ≥N deduped
  companies, each reaching `profiled` stage.
- Every opportunity cites only real signal ids (0 grounding failures).
- Every displayed fact is labeled OBSERVED/INFERRED/UNKNOWN and every important fact has
  an evidence row with source + timestamp.
- Dashboard filters/sorts/paginates; a reviewer can save/reject/tag/advance a prospect.
- Outreach drafts reference at least one observed signal and name a concrete outcome (not
  "AI").
- robots.txt is honored; no disallowed platform is scraped; per-provider rate budgets
  hold.

## 5. Adding the next vertical (proves the architecture)

Because verticals are data (`verticals.config`) and sources are providers, the second
vertical (e.g. dental clinics or property management) should require: a config row
(keywords, scoring-weight overrides), possibly one new `DiscoveryProvider`, and vertical-
specific signal codes — **no core rewrite.** This is the explicit test of modularity.
