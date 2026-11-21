# Project Q — Campaign Economics and On-Chain DeFi

> **Public product and engineering case study.** The implementation repository is private. This document describes reviewed design and engineering scope without disclosing privileged operations or claiming an unverified production release.

**Founding developer:** [Thomas Phillips](https://github.com/darealrektrush)

[Personal engineering profile](../README.md) · [CrabStar Ecosystem](https://github.com/CrabStar-Ecosystem) · [Original engineering showcase](../showcases/project-q.md)

## Executive summary

Project Q is CrabStar's reusable economic engine. It turns identity-backed, verified participation into campaign-specific eligibility, deterministic scoring, allocations and traceable economic outcomes. Its on-chain/DeFi direction includes wallet and token-aware rules, SPL/Token-2022/USDC workflows, distributions, burns, settlement verification and receipts. Strategic airdrops remain deferred.

## Problem and engineering approach

**Key engineering challenge:** Keep campaign calculations, financial approval, execution and settlement evidence separate. An allocation is not a completed transfer; a successful test is not proof of production activation.

## Architecture, tradeoffs and representative scenario

### The problem

Community campaigns often scatter eligibility, missions, scoring and payouts across messages, spreadsheets and one-off scripts. Participants struggle to see their next step; operators struggle to reconcile what happened.

Q brings those responsibilities into a campaign system that can be reused across assets and interfaces.

### A practical engineering scenario

A contribution arrives twice. Its campaign result is recorded, but payment confirmation has not arrived. The interface must preserve the participant's progress without displaying a completed payout.

That scenario drives three design choices: distinguish duplicate input from new participation, keep calculation separate from execution, and make recorded outcomes distinguishable from confirmed settlement.

### Responsibility map

```mermaid
flowchart TD
    T["Telegram campaign client"] --> Q["Q campaign services"]
    U["Future Universe client"] -. "shared service integration" .-> Q
    O["Oracle identity facts"] --> Q
    B["Contribution evidence"] --> Q
    Q --> R["Campaign decisions and records"]
    E["Separately authorized execution"] --> S["Settlement evidence"]
    R --> V["Receipt and reconciliation views"]
    S --> V
```

This is a responsibility map, not an execution protocol or live deployment diagram. A campaign decision does not grant execution authority.

### Decisions and tradeoffs

| Decision | Why it matters | Cost to manage |
| --- | --- | --- |
| Oracle owns identity; Q consumes verified facts | Campaigns can reuse one persistent profile | Cross-service integration needs explicit verification |
| Campaign records and settlement remain distinct | A proposed reward cannot masquerade as a paid reward | More states to explain in the participant interface |
| Reconcile outcomes against evidence | Repeated delivery and partial outcomes stay reviewable | Recovery and disagreement paths need dedicated handling |

### Scope

| Area | Product responsibility |
| --- | --- |
| Operations | Campaign definitions, participant journeys and mission progression |
| Eligibility and scoring | Campaign-specific decisions using verified identity facts |
| Economics | Allocation, release and settlement policy |
| Contribution | Reviewable evidence from connected contribution platforms |
| Receipts | Attributable economic outcomes and participant history |

Oracle owns permanent identity, account/wallet verification and lifetime reputation. Q owns campaign-specific decisions. Universe consumes those services; Bagwork integration connects contribution to the campaign experience.

### Engineering substance

The implementation repository contains a Node.js/Express service, Telegram campaign application, campaign logic, economic modules, database migrations and automated tests.

Engineering work includes separating campaign calculation from financial execution, preserving attributable results, handling repeated delivery and representing partial outcomes explicitly. Generic operation, contribution and receipt integrations remain active development.

A calculation result is not transaction authorization. A recorded allocation is not proof of a finalized payment. The product experience must explain those distinctions clearly.

Representative private-source tests cover identity authority, deterministic allocation inventory, duplicate-credit rejection and the distinction between allocation, release and settlement receipts. This is source review of selected tests, not a report that the complete campaign journey has passed hosted verification.

For an inspectable public illustration of repeated and out-of-order observations, see the [Event Reconciliation Lab](../examples/event-reconciliation/README.md). It uses synthetic records and does not reproduce Q's production rules.

### Current stage

Active development and integration. FAWKQ is the current proving asset and Bond the Duck is a reference campaign. Code, open PRs, deployment and campaign activation are separate states; this showcase does not certify a live reward program.

The first campaign surface is the Project Q Telegram Mini App. Universe is intended to reuse the same engine and canonical identity.

### Direction

Build reusable participation and economic coordination across campaigns, contribution programs and ecosystem products. Broader airdrop, burn and settlement mechanics require their own validation and release review.



## Development ownership

**Founding developer:** [Thomas Phillips](https://github.com/darealrektrush)

This work combines product and architecture decisions, iterative implementation, integration review, verification and operational tradeoffs. Collaborative credit identifies shared development without equating authorship of distinct systems.

## Current evidence boundary

Active integration and Dev acceptance work; financial settlement and on-chain mechanics must be described by specific verified environments, not assumed generally available.

The private implementation repository is [Project-Q-](https://github.com/CrabStar-Ecosystem/Project-Q-). Code, working prototypes, test results, deployed services, actual settlements and released product availability are distinct kinds of evidence.

## Publication boundary

This page intentionally excludes secrets, sensitive system details, private participant records, strategy parameters and transaction authorization configuration.
