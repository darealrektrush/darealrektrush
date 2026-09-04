# Deliverable 2 — Database Schema

Target: **Supabase Postgres 17** (org *Project Q*). Uses `pgvector` for evidence/company
dedupe and semantic search, `pg-boss` for the queue (its own schema), and RLS for the
internal team. Below is the logical model plus reference DDL. This is a **proposal** — no
migration has been applied.

## 1. Entity overview

```
verticals ──< discovery_queries ──< companies ──< company_locations
                                        │
   companies ──< contacts               ├──< technologies
   companies ──< signals                ├──< reviews_summary
   companies ──< opportunities ──< opportunity_integrations
   companies ──< scores (1:1 latest)    ├──< job_postings
   companies ──< outreach_drafts        └──< evidence  (polymorphic, links everything)
   companies ──< prospect_status (pipeline) ──< prospect_activity (audit trail)
```

Design choices:
- **`evidence` is the provenance spine.** Almost every other table references an
  `evidence_id` (or is referenced by evidence via `subject_type/subject_id`) so any fact
  can show its source URL, snapshot, and timestamp.
- **Truth labeling is a column**, not a convention: `truth truth_label` enum on every
  derived fact (`OBSERVED | INFERRED | UNKNOWN`).
- **Confidence is a column** (`numeric(4,3)` 0–1) wherever a value is inferred.
- **Scores are versioned** (`scoring_model_version`) so re-scoring is auditable.

## 2. Enums

```sql
create type truth_label       as enum ('OBSERVED','INFERRED','UNKNOWN');
create type company_stage      as enum ('discovered','enriched','analyzed','scored','profiled','error');
create type pipeline_status    as enum ('new','reviewing','saved','rejected','assigned','contacted','replied','won','lost');
create type complexity_level   as enum ('LOW','MEDIUM','HIGH');
create type automation_category as enum (
  'LEAD_AUTOMATION','CUSTOMER_SUPPORT','AI_RECEPTIONIST','APPOINTMENT_AUTOMATION',
  'CRM_AUTOMATION','SALES_FOLLOWUP','CUSTOMER_ONBOARDING','DOCUMENT_PROCESSING',
  'INTERNAL_OPERATIONS','REPORTING','MARKETING_AUTOMATION','REVIEW_REPUTATION',
  'PAYMENT_INVOICE','EMPLOYEE_WORKFLOWS','COMMUNITY_AUTOMATION','DATA_INTELLIGENCE',
  'AI_AGENTS','CUSTOM_SOFTWARE_INTEGRATION');
create type signal_kind        as enum ('OPERATIONAL','PAIN','GROWTH','TECH');
```

## 3. Core tables (reference DDL)

```sql
-- Verticals are data, not code, so new industries are added without a deploy.
create table verticals (
  id            text primary key,          -- 'home_services'
  label         text not null,
  parent_id     text references verticals(id),
  config        jsonb not null default '{}',-- keywords, discovery hints, scoring weights
  is_active     boolean not null default true,
  created_at    timestamptz not null default now()
);

create table discovery_queries (
  id            uuid primary key default gen_random_uuid(),
  vertical_id   text not null references verticals(id),
  params        jsonb not null,             -- {geo, category, size, min_reviews, ...}
  provider      text not null,              -- which DiscoveryProvider ran
  status        text not null default 'pending',
  requested_by  uuid,                       -- app user
  created_at    timestamptz not null default now(),
  completed_at  timestamptz
);

create table companies (
  id                uuid primary key default gen_random_uuid(),
  vertical_id       text not null references verticals(id),
  discovery_query_id uuid references discovery_queries(id),
  name              text not null,
  website_url       text,
  website_domain    text,                   -- normalized, for dedupe
  external_ids      jsonb not null default '{}', -- {google_place_id, yelp_id, ...}
  industry          text,
  business_model    text,
  size_estimate     text,                   -- '1-10','11-50',...
  size_truth        truth_label not null default 'UNKNOWN',
  hq_location       text,
  location_count    int,
  stage             company_stage not null default 'discovered',
  first_seen_at     timestamptz not null default now(),
  last_enriched_at  timestamptz,
  last_analyzed_at  timestamptz,
  dedupe_embedding  vector(1536),           -- name+domain+addr, for near-dup detection
  unique (website_domain, name)
);
create index on companies (vertical_id, stage);
create index on companies using ivfflat (dedupe_embedding vector_cosine_ops);

create table company_locations (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  address      text, city text, region text, postal_code text, country text,
  lat double precision, lng double precision,
  is_primary   boolean not null default false
);

create table contacts (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  name         text,
  role         text,                        -- 'owner','office manager', ...
  is_decision_maker boolean,
  email        text, phone text,
  source       text,                        -- where it came from (public listing, site)
  truth        truth_label not null default 'UNKNOWN',
  confidence   numeric(4,3),
  evidence_id  uuid references evidence(id),
  created_at   timestamptz not null default now()
);

create table technologies (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  name         text not null,               -- 'WordPress','Calendly','Jobber',...
  category     text,                        -- 'cms','scheduling','crm','payments',...
  detector     text not null,               -- which TechProvider found it
  truth        truth_label not null default 'OBSERVED',
  confidence   numeric(4,3),
  evidence_id  uuid references evidence(id),
  detected_at  timestamptz not null default now(),
  unique (company_id, name)
);

create table signals (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  kind         signal_kind not null,        -- OPERATIONAL | PAIN | GROWTH | TECH
  code         text not null,               -- 'cta_call_for_quote','no_online_booking',
                                            -- 'slow_response_reviews','admin_hiring', ...
  detail       text,
  weight       numeric(5,2),                -- normalized contribution hint for scoring
  truth        truth_label not null default 'OBSERVED',
  confidence   numeric(4,3) not null default 0.5,
  evidence_id  uuid references evidence(id),
  created_at   timestamptz not null default now()
);
create index on signals (company_id, kind);
create index on signals (code);

create table reviews_summary (
  company_id      uuid primary key references companies(id) on delete cascade,
  source          text,                     -- 'google','yelp'
  review_count    int,
  rating_avg      numeric(3,2),
  themes          jsonb,                    -- extracted complaint/praise themes
  evidence_id     uuid references evidence(id),
  updated_at      timestamptz not null default now()
);

create table job_postings (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  title        text, url text, posted_at date,
  source       text,                        -- compliant source only (see 03-data-sources)
  repetitive_tasks jsonb,                   -- ['scheduling','data entry','follow-up']
  evidence_id  uuid references evidence(id),
  fetched_at   timestamptz not null default now()
);

create table opportunities (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  name         text not null,
  category     automation_category not null,
  current_problem      text not null,
  current_workflow     text,
  proposed_workflow    jsonb not null,      -- ordered steps
  business_impact      text,
  complexity           complexity_level not null,
  confidence           numeric(4,3) not null,
  evidence_signal_ids  uuid[] not null,     -- must reference real signals (grounding)
  llm_model            text,                -- provenance of the generation
  created_at   timestamptz not null default now()
);

create table opportunity_integrations (
  opportunity_id uuid references opportunities(id) on delete cascade,
  technology     text not null,             -- 'Twilio','Jobber','Calendly'
  present        boolean,                   -- already detected on the company?
  primary key (opportunity_id, technology)
);

create table scores (
  id                     uuid primary key default gen_random_uuid(),
  company_id             uuid not null references companies(id) on delete cascade,
  automation_opportunity int not null,      -- 0-100
  commercial_value       int not null,      -- 0-100
  implementation_difficulty int not null,   -- 0-100 (higher = harder)
  confidence             int not null,      -- 0-100
  priority               int not null,      -- 0-100 composite
  breakdown              jsonb not null,     -- per-factor contributions (explainability)
  scoring_model_version  text not null,
  computed_at            timestamptz not null default now()
);
create index on scores (company_id, computed_at desc);

create table outreach_drafts (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  angle        text not null,               -- the observed-evidence hook
  message      text not null,
  channel      text,                        -- 'email','linkedin', ...
  based_on_signal_ids uuid[] not null,      -- grounding
  llm_model    text,
  created_at   timestamptz not null default now()
);

-- Pipeline / CRM-lite state, separate from the immutable intelligence above.
create table prospect_status (
  company_id   uuid primary key references companies(id) on delete cascade,
  status       pipeline_status not null default 'new',
  assigned_to  uuid,
  tags         text[] not null default '{}',
  notes        text,
  updated_at   timestamptz not null default now()
);

create table prospect_activity (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid not null references companies(id) on delete cascade,
  actor        uuid,
  action       text not null,               -- 'status_change','tag_add','note', ...
  detail       jsonb,
  created_at   timestamptz not null default now()
);

-- The provenance spine: every important fact points here.
create table evidence (
  id           uuid primary key default gen_random_uuid(),
  company_id   uuid references companies(id) on delete cascade,
  subject_type text not null,               -- 'signal','technology','contact','review',...
  subject_id   uuid,
  source_type  text not null,               -- 'website','google_places','job_board',...
  source_url   text,
  snapshot_ref text,                        -- object-storage key of the raw capture
  excerpt      text,                        -- the exact matched text, if any
  fetched_at   timestamptz not null default now(),
  robots_allowed boolean,                   -- compliance flag captured at fetch time
  provenance   jsonb not null default '{}'  -- provider, request id, ToS ref
);
create index on evidence (company_id, subject_type);
```

> **Ordering note:** in the actual migration, create `evidence` before the tables that
> FK to it (or add those FKs in a follow-up statement). It is shown last here for
> readability.

## 4. Row-Level Security (RLS)

Internal tool, small trusted team → simplest safe model: enable RLS on all tables and
grant access to authenticated users belonging to an `app_members` allowlist. `assigned_to`
and `requested_by` reference `auth.users`. No public/anon access to any prospect data.

```sql
alter table companies enable row level security;
create policy "members read" on companies for select
  using (auth.uid() in (select user_id from app_members));
-- (repeat per table; writes to prospect_status/activity scoped to members)
```

## 5. Retention & provenance

- `evidence.fetched_at` + `snapshot_ref` give every claim a timestamp and a raw capture.
- A scheduled job marks facts **stale** after N days (per source type) and re-queues the
  company for re-analysis rather than silently trusting old data.
- Personal contact data has its own retention window and a hard-delete path (see
  [07-security-compliance.md](07-security-compliance.md)).
