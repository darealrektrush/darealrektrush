# Project Q
### Verified participation · Campaign economics · On-chain / DeFi infrastructure

**Founding Developer & Technical Lead:** [Thomas Phillips](https://github.com/darealrektrush)

[← Engineering portfolio](../README.md) · [CrabStar Ecosystem](https://github.com/CrabStar-Ecosystem) · [Original engineering showcase](../showcases/project-q.md)

> **Public engineering case study.** Q is an active build. A capability implemented in source or tested in isolation is not automatically deployed, enabled, funded or verified end-to-end. Strategic airdrops remain deferred.

## Executive summary

Project Q is the reusable participation and economic coordination engine for CrabStar. It is designed to let campaigns define what qualifies, what members earn, which asset or economic mechanic applies, and what evidence proves an outcome—all without recreating identity or embedding payout authority in social interactions.

It spans Telegram-based campaigns, verified participation, eligibility, scoring, on-chain/DeFi rules, allocation and settlement records, and integration with ecosystem applications such as Universe and Bagwork.

## The problem

Community campaigns often start as messages, spreadsheets and manual transfers. Once a program crosses multiple products, wallets and assets, that approach becomes difficult to audit. Duplicate actions, missing identity evidence, partial settlement and inaccurate reward displays become real operational risks.

**The engineering goal:** turn social participation and on-chain facts into reproducible campaign decisions, then make the distinction between *earned*, *allocated*, *authorized*, *submitted* and *confirmed* understandable to participants and operators.

## System responsibilities

| Layer | Owner | Responsibility |
| --- | --- | --- |
| Permanent identity, linked accounts and wallets | **Oracle** | Verified identity facts and lifetime Crab Army progression |
| Campaign definitions, eligibility and scoring | **Project Q** | Campaign-specific rules, evidence and decisions |
| Economic mechanics | **Project Q** | Allocation, release, distributions, burns and settlement coordination |
| Financial authorization and chain evidence | **Restricted execution boundary** | Explicit approvals, transactions, finality and reconciliation |
| Member experiences | **Telegram / Universe / connected apps** | Progress, outcomes, actionable status and receipts |

```mermaid
flowchart LR
  A["Member / app action"] --> E["Evidence intake & replay protection"]
  O["Oracle verified identity & wallet facts"] --> G["Eligibility & campaign rules"]
  E --> G
  G --> S["Scoring & allocation record"]
  S --> R["Review / authorization boundary"]
  R -. "approved transaction only" .-> C["Solana execution & finality evidence"]
  S --> V["Participant progress / pending state"]
  C --> L["Reconciliation & settlement receipt"]
  L --> V
```

*Conceptual authority diagram—not a claim that every path is live.*

## On-chain and DeFi mechanics

The product scope is broader than simple social rewards:

- **Token-aware eligibility:** applicable wallet ownership and holdings evidence, including Solana token-program identity, with campaign-specific requirements.
- **Multiple asset paths:** staged SPL / Token-2022 / USDC economic workflows, subject to the exact implementation and release state.
- **Distributions:** reproducible allocation decisions, controlled approval/execution boundaries, confirmation and discrepancy handling.
- **Burn and release logic:** explicit economic rules and records that distinguish a planned action from an executed on-chain result.
- **Holding checkpoints and corrections:** point-in-time eligibility/holding evidence and attributable corrections rather than silent history rewrites.
- **Receipts:** records linking campaign decisions to verifiable settlement evidence where applicable.

**Not yet claimed:** complete live on-chain automation across every asset, universal settlement availability, or strategic airdrops.

## Representative engineering scenario

A member submits the same qualifying action twice. Their campaign allocation is calculated, but no confirmed on-chain payment has been observed.

The correct user experience is **one eligible event**, **one attributable allocation**, and a **pending/unsettled** financial state—not two rewards or a fictional transaction receipt. Retry and reconciliation paths must converge without double credit.

## Design tradeoffs

| Decision | Benefit | Complexity introduced |
| --- | --- | --- |
| Keep Oracle as canonical identity authority | Reusable participation across products | Cross-service claim and ownership validation |
| Separate campaign scoring from transfers | Financial safety and auditability | Multiple explicit lifecycle states |
| Store attributable economic evidence | Reconciliation and dispute handling | More durable records and correction workflows |
| Require verifiable chain settlement | Honest outcome reporting | Provider errors, finality and replay management |
| Keep token mechanisms campaign-scoped | Reusable multi-asset infrastructure | Config validation and security review |

## Engineering substance

The private implementation spans Node.js / Express, Telegram campaign experiences, PostgreSQL / Supabase migrations, Solana integrations and automated checks. Recent development areas include identity integration, referral and participation evidence, holding projections, transaction boundary isolation, and on-chain economic foundations.

Source-level code and individual CI checks establish **engineering progress**. Genuine Dev acceptance, migrations, operator approvals, external wallet behavior and settlement verification require separately recorded evidence.

## My role

As **founding developer and technical lead**, I work across product definition, campaign/economic architecture, service boundaries, implementation, security controls, integration review and release verification. The focus is to make economic participation useful, understandable and independently auditable.

## Current stage and publication boundary

**Status: active development and integration.** FAWKQ has served as a proving environment for campaign mechanics. Future campaigns and economic operations require their own authorization and live verification.

This public document intentionally excludes privileged payout procedures, campaign budgets, private account data, production configuration and unreleased operational details.

**Participation with purpose. Outcomes with evidence.**
