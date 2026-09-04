# Deliverable 7 — Security & Compliance Considerations

This platform handles business data and some personal data (public business contacts,
possibly decision-maker names/emails). It must be lawful, respectful of source terms, and
secure. Compliance is built into the pipeline, not bolted on.

## 1. Data-collection compliance

| Rule | How it's enforced |
|------|-------------------|
| **Respect robots.txt** | Crawler checks robots before every fetch; honors `Disallow` and crawl-delay; records `robots_allowed` on each `evidence` row. Disallowed paths are skipped, not fetched. |
| **Only crawl the target's own public site** | Discovery/enrichment of third-party platforms uses their **APIs**, never HTML scraping of LinkedIn/Indeed/Google/Yelp result pages. |
| **Honor API terms & caching limits** | Each provider declares its ToS posture; notably Google Places field-caching/attribution limits are respected in storage and display. |
| **Rate limits** | Per-provider `RateBudget` enforced by the queue (token-bucket); backoff on 429/5xx. |
| **No auth/paywall bypass** | Crawler fetches only anonymous, public pages. No logins, no paywalls, no CAPTCHA solving. |
| **Descriptive User-Agent** | Identifies the crawler with a contact URL. |

## 2. Privacy & personal data

- **Lawful basis / minimization.** Store personal contact data only where **publicly and
  lawfully available**, and only fields needed for B2B outreach. Decision-maker data is
  opt-in per prospect, never bulk-harvested.
- **Provenance on personal data.** Every contact row has `source`, `evidence_id`,
  `truth`, `confidence`. Unknown ⇒ `UNKNOWN`, never fabricated.
- **Data-subject rights (GDPR/CCPA-style).** A hard-delete path removes a company and all
  personal data + evidence; a suppression list prevents re-adding opted-out contacts.
- **Retention.** Personal contact data has a bounded retention window; stale facts are
  re-verified or expired rather than trusted indefinitely.
- **Anti-spam (CAN-SPAM / CASL).** The platform **generates** outreach drafts; it does
  not send bulk mail. Any future sending must include identification + opt-out and honor
  suppression. MVP keeps a human in the loop for every send.

## 3. Application security

| Area | Measure |
|------|---------|
| **AuthN/Z** | Supabase Auth; internal-only; `app_members` allowlist; RLS on every table (no anon/public read of prospect data). |
| **Secrets** | API keys in Vercel/Render env + Supabase Vault; never in the repo; least-privilege keys per provider. |
| **Transport** | HTTPS everywhere; outbound honors the environment proxy/CA bundle. |
| **Input handling** | Crawled HTML is untrusted: parse in the worker, never execute; sanitize before rendering any excerpt in the dashboard (XSS). |
| **LLM prompt-injection** | Crawled/review/job text is untrusted. The Analyzer receives it as clearly delimited *data*, with instructions that this content cannot change the task; outputs are validated (grounding check + schema) before persistence. Never let scraped text trigger tool calls or config changes. |
| **PII in logs** | Redact contact PII from application logs and LLM request logs. |
| **Audit trail** | `prospect_activity` records who changed pipeline state; `evidence` records data provenance. |
| **Dependency hygiene** | Lockfiles, Dependabot/`npm audit` in CI, pinned provider SDK versions. |

## 4. LLM-specific safeguards

- **No fabrication:** system prompt forbids inventing evidence, contacts, tech, or
  opportunities; the worker rejects opportunities citing non-existent signal ids.
- **Grounded outreach:** outreach must reference ≥1 real observed signal.
- **Cost/abuse controls:** per-run token caps; cheap model (Haiku) for high-volume
  extraction, capable model (Sonnet) only for design/outreach; LLM never sees raw HTML
  dumps.
- **Provider data terms:** confirm business-data usage is permitted under the LLM
  provider's terms; avoid sending unnecessary PII to the model.

## 5. Operational

- Environments separated (dev/prod Supabase projects); migrations reviewed in CI.
- Backups: rely on Supabase automated backups; snapshots (evidence) in versioned storage.
- Kill switch: a global pause flag halts all discovery/crawl jobs if a source complains
  or a rate/ToS issue is detected.

## 6. Explicit "do nots"

- Do **not** scrape platforms that prohibit it.
- Do **not** bypass robots.txt, auth, paywalls, or rate limits.
- Do **not** fabricate any prospect data.
- Do **not** present INFERRED data as OBSERVED fact.
- Do **not** send outreach without human review (MVP) and lawful opt-out (any phase).
