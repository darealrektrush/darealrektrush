# Deliverable 3 — Data-Source Strategy

**Principle:** use *legitimate public/business data sources and permitted APIs*. Prefer
official APIs with clear terms over scraping. Where we crawl, we crawl **only the target
company's own public website**, respecting robots.txt, rate limits, and ToS. We never
scrape platforms that prohibit it (LinkedIn, Google/Yelp result pages, etc.) — we use
their APIs instead. See [07-security-compliance.md](07-security-compliance.md).

Every source is wrapped in a **provider interface** (see [01](01-architecture.md) §4) so
it can be replaced or A/B'd without code changes.

## 1. Discovery (find candidate companies)

| Provider | Use | Terms posture | Cost model |
|----------|-----|---------------|------------|
| **Google Places API** (Text Search / Nearby) | Primary for home-service verticals by category + metro. Returns name, place_id, website, phone, rating, review_count, geo. | Official API; store per Places policy (place_id ok; some fields have caching limits). | Pay per request (see [08](08-costs.md)). |
| **Yelp Fusion API** | Secondary / cross-fill for local services; category taxonomy is strong for contractors. | Official API; display/attribution rules. | Free tier + paid. |
| **Foursquare Places** | Tertiary geo source. | Official API. | Free tier + paid. |
| **OpenStreetMap / Overture** | Free geo baseline, coverage varies. | Open data. | Free. |
| **Web3/crypto** (later vertical) | Chain explorers, protocol registries, public grant/ecosystem lists, GitHub org signals. | Public/on-chain. | Mostly free. |

MVP uses **Google Places** as the single active `DiscoveryProvider`; Yelp is the
first drop-in alternative to validate the abstraction.

## 2. Website intelligence (own crawler)

- **What:** fetch and, where needed, render the company's public site; extract forms,
  quote/booking flows, live chat, phone/email-first CTAs, FAQ, application forms, PDFs,
  scheduling, portals, socials, locations, services, and CTAs.
- **How:** cheap `fetch` first; escalate to **Playwright (pre-installed Chromium on
  Render)** only when the page is JS-rendered. Respect `robots.txt`, set a descriptive
  User-Agent, honor crawl-delay, cap pages/site, and snapshot each fetched page to object
  storage (evidence). No login walls, no paywalls, no non-public areas.

## 3. Technology detection

| Provider | Use | Cost |
|----------|-----|------|
| **In-house heuristics** | Match markup/scripts/headers/DNS against a fingerprint set (CMS, chat widgets, scheduling, CRM, payments, analytics). Zero marginal cost, fully in our control. | Free |
| **Wappalyzer (self-host ruleset / API)** | Broader coverage without maintaining fingerprints. | Free ruleset / paid API |
| **BuiltWith API** | Deepest historical tech + spend estimates. | Paid |

MVP: **in-house heuristics** (covers the tech list in the brief: WordPress, Shopify,
HubSpot, Calendly, Stripe, Square, Intercom, Zendesk, GoHighLevel, Jobber, ServiceTitan,
etc.), with BuiltWith as a later paid enrichment for high-priority prospects only.

## 4. Enrichment (firmographics, contacts, decision-maker)

| Provider | Use | Notes |
|----------|-----|-------|
| **Own crawl** (contact/about pages) | Public business email/phone, owner name, services. | Primary; fully evidence-backed. |
| **Google Places details** | Phone, hours, website, rating. | Already fetched at discovery. |
| **People/company data API** (e.g., Clearbit-class, PDL, Hunter for role emails) | Fill decision-maker + role email *where lawfully available*. | Paid; opt-in per prospect; store provenance; respect their ToS and privacy law. |
| **Company registries** (Secretary of State, Companies House) | Legal entity, officers. | Public; free/low cost. |

Decision-maker data is only stored when **lawfully and publicly available**, always with
`truth`/`confidence` and evidence. Missing ⇒ `UNKNOWN`, never fabricated.

## 5. Pain signals — reviews & job postings

- **Reviews:** Google Places / Yelp review **summaries** (count, rating, extracted
  themes) via their APIs — used for *volume* and *complaint-theme* signals (slow
  response, scheduling, communication). We store summaries/themes, not verbatim scraped
  review corpora beyond API terms.
- **Job postings (high value per the brief):** use **compliant** sources only —
  - the company's **own careers page** (own crawl), and
  - **Google Jobs via a licensed SERP API** or official job-board APIs.
  - **Not** LinkedIn/Indeed scraping. We analyze descriptions for repetitive tasks
    (answering inquiries, scheduling, data entry, CRM updates, lead qualification,
    follow-up, reporting, document processing, appointment confirmation, moderation) and
    convert them into `PAIN`/`OPERATIONAL` signals → automation opportunities.

## 6. Source-selection rules

1. **Prefer official APIs** over scraping, always.
2. **Only crawl the target's own site**; never crawl a third-party platform that forbids it.
3. **One active provider per capability in MVP**, ≥1 alternative implemented to prove
   replaceability.
4. **Every fetched fact → an `evidence` row** with source, URL, snapshot, timestamp, and
   `robots_allowed`.
5. **Respect caching/attribution limits** of each API (notably Google Places field
   caching rules).

## 7. Provider matrix (MVP vs. later)

| Capability | MVP active | Alt implemented | Later / paid |
|------------|-----------|-----------------|--------------|
| Discovery | Google Places | Yelp Fusion | Foursquare, OSM |
| Crawl | fetch + Playwright | — | — |
| Tech detect | in-house heuristics | Wappalyzer ruleset | BuiltWith API |
| Enrichment | own crawl + Places details | registries | PDL / Hunter |
| Reviews | Google Places summaries | Yelp | — |
| Jobs | own careers page | Google Jobs (SERP API) | job-board APIs |
| LLM | Claude Haiku + Sonnet | (any `LLMProvider`) | — |
