# Deliverable 4 — Opportunity-Scoring Model

The Scoring Engine is **deterministic and explainable** (no LLM). The LLM proposes
automation opportunities; this engine scores the company and the opportunities from the
underlying signals so scores are stable, cheap to recompute, and auditable. Every score
stores a per-factor `breakdown` (see `scores.breakdown` in [02](02-database-schema.md))
and a `scoring_model_version`.

## 1. The five outputs (per the brief)

| Output | Range | Meaning |
|--------|-------|---------|
| **Automation Opportunity Score** | 0–100 | How much automatable manual work exists. |
| **Commercial Value Score** | 0–100 | Size of the money on the table. |
| **Implementation Difficulty** | 0–100 | Effort/risk to deliver (higher = harder). |
| **Confidence Score** | 0–100 | How well-evidenced the above are. |
| **Overall Prospect Priority** | 0–100 | The single number the team sorts by. |

## 2. Factor inputs (from the brief)

Each factor is normalized to 0–1 from `signals`, `technologies`, firmographics, reviews,
and job postings, then weighted. Missing inputs contribute 0 to the value **and** lower
the Confidence score (they do not silently inflate a score).

| # | Factor | Feeds | Derived from |
|---|--------|-------|--------------|
| F1 | Manual Workflow Evidence | Opportunity, Difficulty(−) | `signals` PAIN/OPERATIONAL codes (call-for-quote, no online booking, download-form intake) |
| F2 | Lead Volume Potential | Opportunity, Value | review_count, service-area size, location_count |
| F3 | Repetitive Work | Opportunity | job-posting repetitive tasks, FAQ size |
| F4 | Customer Communication Volume | Opportunity, Value | phone/email-first CTAs, chat presence, review volume |
| F5 | Company Size | Value, Difficulty(+) | size_estimate, location_count |
| F6 | Growth Signals | Value | hiring activity, new locations, expansion language |
| F7 | Hiring Signals (admin) | Opportunity, Value | admin/receptionist/coordinator job postings |
| F8 | Existing Technology | Difficulty(−), Confidence | detected CRM/scheduling/payments (integration-ready) |
| F9 | Ease of Integration | Difficulty(−) | presence of API-friendly tools (Calendly, Stripe, Jobber, HubSpot) |
| F10 | Estimated ROI | Value | modeled from F2×F3×F4 and size |
| F11 | Implementation Complexity | Difficulty(+) | opportunity `complexity`, custom-integration need |
| F12 | Ability to Reach Decision Maker | Value, Confidence | contact/decision-maker availability + truth label |

## 3. Formulas

Let each factor `Fi ∈ [0,1]`. Composite sub-scores are weighted sums, clamped to 0–100.
Weights below are the **v1 defaults** (tunable per vertical via `verticals.config`).

```
Automation Opportunity =
  100 * ( 0.30*F1 + 0.20*F3 + 0.20*F4 + 0.15*F2 + 0.10*F7 + 0.05*F6 )

Commercial Value =
  100 * ( 0.30*F10 + 0.25*F2 + 0.20*F5 + 0.15*F6 + 0.10*F12 )

Implementation Difficulty =                       # higher = harder
  100 * ( 0.40*F11 + 0.25*(1-F9) + 0.20*(1-F8) + 0.15*normalize(F5_size_complexity) )

Confidence =
  100 * ( 0.50*evidence_coverage + 0.30*avg_signal_confidence + 0.20*F12_truth )
        # evidence_coverage = share of scored factors backed by OBSERVED evidence
```

### Priority (the sort key)

Priority rewards opportunity and value, discounts difficulty, and is scaled by
confidence so poorly-evidenced prospects don't top the list:

```
raw = 0.45*AutomationOpportunity + 0.40*CommercialValue - 0.15*ImplementationDifficulty
Priority = clamp0_100( raw * (0.5 + 0.5*(Confidence/100)) )
```

Interpretation bands: **80–100** hot · **60–79** strong · **40–59** worth a look ·
**<40** deprioritize.

## 4. Worked example (roofing contractor)

Signals: "Call for quote" CTA (F1), no online booking (F1), Google reviews = 480 (F2,F4),
3 locations (F2,F5), careers page hiring an "office coordinator / scheduler" (F3,F7),
detected WordPress + no CRM/scheduling (F8 low, F9 low), public owner name + email (F12).

| Sub-score | Value | Why |
|-----------|-------|-----|
| Automation Opportunity | ~82 | strong manual-workflow + comms + hiring evidence |
| Commercial Value | ~71 | high lead volume, multi-location, ROI |
| Implementation Difficulty | ~55 | greenfield (no tools to integrate = build more) |
| Confidence | ~76 | most factors OBSERVED with evidence |
| **Priority** | **~74 (strong)** | high opp+value, moderate difficulty, good confidence |

The `breakdown` JSON records each Fi and its contribution so the detail view can explain
*why* the score is what it is.

## 5. Opportunity-level confidence

Each `opportunities` row carries its own `confidence` (from the LLM, validated by the
grounding check that every cited signal exists). A company's Confidence sub-score does
**not** inherit the LLM's self-reported confidence blindly — it is driven by evidence
coverage and signal confidence, so a confident-sounding but thinly-evidenced opportunity
still scores low on Confidence.

## 6. Calibration plan

- v1 weights are expert priors. After ~2–3 weeks of human review in the dashboard,
  compare Priority against reviewer accept/reject to fit weights (simple logistic
  regression on the factor vector → probability of "saved/won").
- Weights live in `verticals.config`, so re-tuning per vertical is a data change, and
  `scoring_model_version` keeps historical scores comparable.
