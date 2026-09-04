# Deliverable 8 — Estimated API / Service Costs

> **All figures are planning estimates, order-of-magnitude, in USD.** Provider prices
> change — verify against live pricing pages before committing. Estimates assume the MVP
> (single home-service vertical) and reuse of infrastructure already on this account
> (Supabase org *Project Q*, Vercel hobby team, Render workspace).

## 1. Fixed monthly platform cost (MVP)

| Service | Tier | Est. / mo |
|---------|------|-----------|
| Supabase | Free during build → Pro when past free limits | $0 → **$25** |
| Vercel | Hobby (present) — fine for internal dashboard | **$0** (Pro $20 if needed) |
| Render | 1 worker service + 1 cron (starter/standard) | **$7–$25** |
| Object storage (snapshots) | Supabase Storage (within Pro) | included → low |
| **Fixed subtotal** | | **~$10–$50 / mo** |

Vercel hobby is adequate for a small internal team; move to Pro only if you need
team seats or higher limits.

## 2. Variable cost — per-provider, per 1,000 companies processed

Assumes discovering and fully processing 1,000 companies end to end.

### Discovery (Google Places)
- Text/Nearby Search returns ~20 results/call → ~50–120 calls to surface 1,000
  candidates (with filtering/dedup overhead).
- Place Details (website, phone, rating) for ~1,000 companies.
- **Est: ~$25–$60 / 1,000 companies.** (Google provides recurring monthly free credit
  that offsets low volumes.)

### Crawling & tech detection
- Own crawler on Render; marginal cost ≈ compute already in the fixed worker.
- **Est: ~$0 marginal** (in-house heuristics; no per-call API).

### Reviews & jobs (MVP)
- Review **summaries** via Places/Yelp (Yelp Fusion has a free tier); careers-page jobs
  via own crawl. **Est: ~$0–$15 / 1,000.**
- *Optional* Google Jobs via SERP API (if enabled later): SERP APIs run
  ~$25–$75 per 5k searches → budget separately if turned on.

### LLM (Claude) — the main variable cost
Two-model strategy: **Haiku** for high-volume extraction/classification, **Sonnet** for
opportunity design + outreach. LLM only sees *distilled signals*, not raw HTML.

Rough per-company token budget:
- Haiku (light classification/normalization): ~2k in / ~0.5k out.
- Sonnet (opportunity design): ~6k in / ~2k out.
- Sonnet (outreach draft): ~2k in / ~0.6k out.

Using approximate list prices (Haiku ≈ $1/$5, Sonnet ≈ $3/$15 per 1M input/output
tokens — **verify current pricing**):
- Haiku ≈ $0.004 / company
- Sonnet design ≈ $0.048 / company
- Sonnet outreach ≈ $0.015 / company
- **≈ $0.05–$0.08 / company → ~$50–$80 / 1,000 companies.**

Prompt caching on the shared system prompt/schema and batching lower this further at
volume; run outreach only for prospects a human decides to pursue to cut it more.

### Optional paid enrichment (later, high-priority prospects only)
- BuiltWith API, PDL/Clearbit-class person data, Hunter role emails: typically
  **$0.01–$0.50 per lookup** depending on provider/tier — apply selectively, not to the
  whole funnel.

## 3. Blended MVP cost example

Processing **1,000 companies/month**, MVP sources only:

| Bucket | Est / mo |
|--------|----------|
| Fixed platform | $10–$50 |
| Google Places (discovery + details) | $25–$60 |
| Reviews/jobs (MVP, mostly free tiers) | $0–$15 |
| LLM (Claude, 2-model) | $50–$80 |
| **Total** | **~$85–$205 / mo** |

≈ **$0.09–$0.21 per fully-processed prospect** at this volume. Doubling volume roughly
doubles the variable buckets while fixed costs hold, so unit cost trends down.

## 4. Cost-control levers (built into the design)

1. **Cheap-first pipeline** — deterministic crawl/heuristics/scoring do the heavy lifting;
   the LLM sees only distilled signals.
2. **Two-model LLM split** — Haiku for volume, Sonnet only for design/outreach.
3. **Gate expensive steps** — run outreach generation and paid enrichment only for
   prospects that pass a Priority threshold or human review.
4. **Prompt caching + batching** on the LLM layer.
5. **Rate budgets + staleness windows** — don't re-fetch/re-analyze fresh data; re-run
   only when evidence expires.
6. **Per-provider spend caps** and a cost dashboard fed by request logs, with a global
   pause kill-switch.

## 5. What to verify before committing budget

- Current Google Places SKU pricing + monthly free credit.
- Current Anthropic Claude Haiku/Sonnet token prices and caching discounts.
- Yelp Fusion free-tier limits for review summaries.
- Supabase Pro thresholds (DB size, storage, egress) vs. expected snapshot volume.
- Render service tier sizing for concurrent Playwright crawls.
