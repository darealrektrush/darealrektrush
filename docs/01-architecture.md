# Deliverable 1 — Architecture Proposal

## 1. Design goals

- **Modular & replaceable.** Every external dependency (discovery source, tech
  detector, enrichment provider, LLM) sits behind a provider interface so any single
  API can be swapped without touching business logic.
- **Pipeline as stages.** Each stage is an idempotent job with a typed input and output,
  persisted to the DB before the next stage runs. A crash re-runs only the failed stage.
- **Evidence-first.** Every derived fact links to a row in an audit/evidence table with
  source URL, raw snapshot reference, and timestamp.
- **Cost-aware.** Cheap deterministic extraction runs first; the (expensive) LLM layer
  only sees pre-distilled signals, never raw HTML dumps.

## 2. Component map

```
                        ┌───────────────────────────────────────────────┐
                        │                 DASHBOARD (Next.js/Vercel)      │
                        │  search · filter · pipeline · detail · outreach │
                        └───────────────▲───────────────────────────────┘
                                        │ REST/RPC (Supabase client + route handlers)
                        ┌───────────────┴───────────────────────────────┐
                        │            PROSPECT DATABASE (Supabase PG)      │
                        │  companies · signals · opportunities · scores   │
                        │  contacts · evidence · jobs · outreach          │
                        └───────────────▲───────────────────────────────┘
                                        │ read/write
   ┌──────────────┐   enqueue   ┌───────┴────────┐   dequeue   ┌────────────────────────┐
   │  Scheduler   │────────────▶│   Job Queue     │◀───────────│   Worker pool (Render) │
   │ (Render cron)│             │  (pg-boss / PG) │            │  runs the stage modules │
   └──────────────┘             └─────────────────┘            └───────────┬────────────┘
                                                                           │ calls
        ┌──────────────────────────────────────────────────────────────────┼───────────────┐
        ▼                     ▼                    ▼               ▼         ▼               ▼
 ┌────────────┐      ┌────────────────┐   ┌──────────────┐  ┌──────────┐ ┌──────────┐ ┌──────────────┐
 │ Discovery  │      │ Crawler /      │   │ Technology   │  │ Enrich   │ │ Signal   │ │ LLM          │
 │ Service    │      │ Website        │   │ Detector     │  │ Service  │ │ Extract  │ │ Opportunity  │
 │ (providers)│      │ Analyzer       │   │ (providers)  │  │(providers)│ │ Engine   │ │ Analyzer     │
 └─────┬──────┘      └───────┬────────┘   └──────┬───────┘  └────┬─────┘ └────┬─────┘ └──────┬───────┘
       │                     │                   │               │            │              │
       └─────────────────────┴───────────────────┴───────────────┴────────────┴──────────────┘
                                        │ every write goes through
                                        ▼
                              ┌────────────────────────┐        ┌────────────────────┐
                              │ Audit / Evidence Layer │        │  Scoring Engine    │
                              │ (source + snapshot + ts)│       │  (deterministic)   │
                              └────────────────────────┘        └────────────────────┘
                                                                          │
                                                                          ▼
                                                                ┌────────────────────┐
                                                                │ Outreach Generator │
                                                                │  (LLM, evidence-fed)│
                                                                └────────────────────┘
```

## 3. The twelve services

| Service | Responsibility | Provider-abstracted? |
|---------|----------------|----------------------|
| **Discovery Service** | Find candidate companies by vertical/geo/filters. | Yes — `DiscoveryProvider` |
| **Crawler / Website Analyzer** | Fetch & render public pages (robots-aware), extract DOM signals: forms, CTAs, booking, chat, phone/email-first workflows, service list, locations. | Fetch layer swappable (fetch vs. Playwright) |
| **Technology Detector** | Identify publicly detectable tech (CMS, chat, CRM, payments, scheduling) from markup, headers, script hosts. | Yes — `TechProvider` (heuristics / BuiltWith / Wappalyzer) |
| **Enrichment Service** | Firmographics, size estimate, socials, public contacts, decision-maker where lawful. | Yes — `EnrichmentProvider` |
| **Signal Extraction Engine** | Normalize raw crawl/enrich/review/job data into typed `signals` (operational + pain), each with evidence + confidence. Deterministic + light NLP. | Internal |
| **LLM Opportunity Analyzer** | Turn distilled signals into concrete automation workflows (the structured object below). | Yes — `LLMProvider` |
| **Scoring Engine** | Deterministic, explainable scores from signals + opportunities (no LLM). | Internal |
| **Prospect Database** | System of record. | Supabase Postgres |
| **Dashboard** | Internal UI: search/filter/sort/review/pipeline. | Next.js |
| **Outreach Generator** | Evidence-grounded outreach angle + message. | `LLMProvider` |
| **Job Queue / Scheduler** | Orchestrate stages, retries, backoff, rate-limit budgets per provider. | pg-boss → BullMQ |
| **Audit / Source Evidence Layer** | Persist source + timestamp + raw snapshot pointer for every important fact. | Internal + object storage |

## 4. Provider abstraction (the key to "replaceable")

Every external capability is an interface with 1..n implementations, selected by config.
Example (TypeScript):

```ts
export interface DiscoveryProvider {
  readonly id: string;                     // "google_places", "yelp", ...
  supports(vertical: Vertical): boolean;
  discover(q: DiscoveryQuery): AsyncIterable<CandidateCompany>;
  readonly rateLimit: RateBudget;          // enforced by the queue
  readonly terms: { robotsRespected: boolean; tos: string };
}

export interface TechProvider   { detect(site: SiteSnapshot): Promise<TechFinding[]>; }
export interface EnrichmentProvider { enrich(c: Company): Promise<EnrichmentResult>; }
export interface LLMProvider    { analyze(p: AnalyzerPrompt): Promise<OpportunitySet>; }
```

A `ProviderRegistry` resolves the active implementation per capability from environment
config, so switching (e.g.) Google Places → Yelp is a config change, not a code change.
Providers declare their own rate budget and ToS/robots posture; the queue enforces them.

## 5. Stage contract (idempotency & evidence)

Each stage:

1. Reads its input row(s) by `company_id`.
2. Does its work behind a provider interface.
3. Writes typed output rows **and** an `evidence` row (`source_url`, `snapshot_ref`,
   `fetched_at`, `provenance`) for each important fact.
4. Marks the stage `status` on the company (`discovered → enriched → analyzed → scored →
   profiled`) so re-runs are safe and progress is queryable.

Every derived value carries a **confidence** (0–1) and a **truth label**
(`OBSERVED | INFERRED | UNKNOWN`). The Scoring Engine and UI consume these directly.

## 6. The LLM Opportunity object (the required output)

The analyzer is prompted with **only distilled signals + tech + firmographics** (never
raw HTML) and must return, for each proposed automation:

```jsonc
{
  "automation_name": "Inbound Lead Qualification & Routing",
  "category": "LEAD_AUTOMATION",
  "current_problem": "Estimate requests arrive via a 'Call for quote' CTA with no online intake.",
  "evidence": ["signal:cta_call_for_quote#123", "signal:no_online_booking#124"],
  "current_likely_workflow": "Caller leaves voicemail → office returns call → manual notes.",
  "proposed_workflow": ["Web/SMS intake", "AI qualification", "CRM entry", "estimate booking", "reminders", "follow-up", "review request"],
  "recommended_integrations": ["Twilio", "Jobber", "Calendly"],
  "implementation_complexity": "MEDIUM",
  "potential_business_impact": "Faster response, fewer missed leads, more booked estimates.",
  "confidence": 0.72
}
```

Guardrails: the prompt forbids inventing evidence; every `evidence[]` entry must
reference a real `signals` row id, and the worker rejects/repairs outputs that cite
non-existent evidence (grounding check before persistence).

## 7. Data flow, end to end

1. **Discovery** enqueues candidate companies for a `{vertical, geo, filters}` query.
2. **Enrichment** attaches firmographics/contacts/socials.
3. **Crawler** snapshots the site (respecting robots.txt); **Tech Detector** runs on the
   snapshot.
4. **Signal Extraction** converts everything into `signals` (operational + pain) with
   evidence. Reviews and public job postings feed pain signals here.
5. **LLM Analyzer** produces `opportunities` (grounded in signal ids).
6. **Scoring Engine** computes the five scores + priority deterministically.
7. **Prospect** assembly writes the profile; **Outreach Generator** drafts the angle.
8. Row appears in the **Dashboard**, ready for human review and pipeline management.

## 8. Why this topology (trade-offs)

- **Postgres-first (pg-boss) queue for MVP** avoids running Redis; the DB is already the
  bottleneck of record. Swap to BullMQ + Render Key-Value when concurrency > a few dozen
  crawlers or when queue volume dominates DB load.
- **Crawling on Render, UI on Vercel.** Vercel functions cap execution time and are
  awkward for headless-browser workloads; Render worker services run long, use the
  pre-installed Chromium, and scale independently of the UI.
- **LLM sees signals, not HTML.** Keeps token cost bounded and output grounded; the
  cheap deterministic layer does the heavy lifting first.
- **Deterministic scoring (no LLM).** Scores must be explainable, stable, and cheap to
  recompute; the LLM proposes opportunities, the engine scores them.
