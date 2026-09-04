# Deliverable 6 — Recommended Repository Structure

A **TypeScript monorepo** (pnpm workspaces + Turborepo). One language across UI, API,
workers, and providers keeps the shared domain types (the pipeline contracts) in one
place, which is what makes the "replaceable provider" design actually hold together.

```
automation-opportunity-engine/
├─ apps/
│  ├─ web/                    # Next.js (App Router) dashboard + API route handlers → Vercel
│  │  ├─ app/
│  │  │  ├─ (dashboard)/prospects/         # list: search/filter/sort/pipeline
│  │  │  ├─ (dashboard)/prospects/[id]/    # detail view (11 sections + evidence)
│  │  │  └─ api/                           # thin RPCs; heavy work is enqueued
│  │  └─ components/
│  └─ worker/                 # long-running stage runner → Render worker service
│     └─ src/
│        ├─ index.ts          # pg-boss consumer; registers stage handlers
│        └─ stages/           # discover, enrich, crawl, detect-tech, extract-signals,
│                             #   analyze-llm, score, assemble-profile, outreach
│
├─ packages/
│  ├─ core/                   # domain model & pipeline contracts (no I/O)
│  │  ├─ types/               # Company, Signal, Opportunity, Score, Evidence, ...
│  │  ├─ scoring/             # deterministic Scoring Engine (04-scoring-model)
│  │  └─ pipeline/            # stage interfaces, Stage<TIn,TOut>, orchestration types
│  ├─ providers/              # ALL replaceable external integrations
│  │  ├─ registry.ts          # resolves active impl per capability from config
│  │  ├─ discovery/           # google-places/, yelp/, foursquare/  (DiscoveryProvider)
│  │  ├─ tech/                # heuristics/, wappalyzer/, builtwith/ (TechProvider)
│  │  ├─ enrichment/          # crawl/, registries/, pdl/           (EnrichmentProvider)
│  │  ├─ reviews/             # google/, yelp/
│  │  ├─ jobs/                # careers-crawl/, serp-jobs/
│  │  └─ llm/                 # anthropic/  (LLMProvider: analyze + outreach)
│  ├─ crawler/               # robots-aware fetch + Playwright fallback + snapshotting
│  ├─ signals/              # deterministic Signal Extraction Engine + signal codes
│  ├─ db/                    # Supabase client, generated types, repositories
│  ├─ queue/                 # pg-boss setup, job defs, rate-budget middleware
│  ├─ evidence/              # provenance helpers (write source+snapshot+timestamp)
│  └─ config/                # env schema (zod), provider selection, vertical loader
│
├─ supabase/
│  ├─ migrations/            # SQL from 02-database-schema.md
│  └─ seed/                  # verticals rows (home_services), signal-code catalog
│
├─ docs/                     # THIS planning set (00–08)
├─ infra/                    # render.yaml, vercel.json, deployment notes
├─ .github/workflows/        # lint, typecheck, test, migrate-check
├─ turbo.json  pnpm-workspace.yaml  package.json  tsconfig.base.json
└─ README.md
```

## Why this shape

- **`packages/core` has no I/O.** Domain types, the scoring engine, and stage interfaces
  live here so both the worker and the web app depend on the same contracts. Scoring is
  unit-testable with zero mocks.
- **`packages/providers` is the replaceability boundary.** Every external API is one
  subfolder implementing one interface; `registry.ts` picks the active one from config.
  Swapping Google Places → Yelp = change an env var. Adding BuiltWith = add a folder.
- **`apps/worker` vs `apps/web` split matches the runtime split** (Render workers do
  crawling/LLM; Vercel serves the dashboard). They share `packages/*`.
- **`packages/evidence` is used by every stage**, enforcing "source + timestamp on every
  important fact" in one place instead of by convention.
- **Verticals & signal codes are seed data**, not code — new verticals are added by data.

## Deployment mapping

| Package/app | Runs on |
|-------------|---------|
| `apps/web` | Vercel (hobby team present) |
| `apps/worker` | Render worker service (uses pre-installed Chromium) |
| queue + DB + storage | Supabase (Postgres + Storage), org *Project Q* |
| scheduler | Render cron → enqueues discovery / staleness re-runs |

## Placement in this GitHub repo

This planning set lives under `docs/` on branch
`claude/automation-opportunity-engine-jfu7gg`. When implementation is approved, the
monorepo can be scaffolded either at the repo root of a **dedicated repo** (recommended —
this repo is a personal profile) or under a top-level `app/` directory here. The profile
`README.md` is left untouched.
