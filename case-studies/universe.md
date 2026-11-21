# CrabStar Universe — One Ecosystem Across Web and Mobile

> **Public product and engineering case study.** The implementation repository is private. This document describes reviewed design and engineering scope without disclosing privileged operations or claiming an unverified production release.

**Lead developer:** [Thomas Phillips](https://github.com/darealrektrush)  
**Collaborative developers:** [Thomas Phillips](https://github.com/darealrektrush) and [Andrew](https://github.com/Andrew-07)

[Personal engineering profile](../README.md) · [CrabStar Ecosystem](https://github.com/CrabStar-Ecosystem) · [Original engineering showcase](../showcases/universe.md)

## Executive summary

Universe is CrabStar's unified web and native mobile experience. It brings Oracle-owned identity, intelligence and reputation together with Project Q campaigns, verified participation and economic receipts, while leaving authority for those functions in their respective backend services.

## Problem and engineering approach

**Key engineering challenge:** One canonical profile must stay consistent across devices and product surfaces without duplicating identity, reward balances or wallet-verification authority. Partial connection and unavailable states must be truthful.

## Architecture, tradeoffs and representative scenario

### The problem

Connected infrastructure is difficult to use when people must repeatedly switch tools, reconnect accounts and piece together their history.

Universe is intended to give those shared services one coherent experience while preserving their independent responsibilities.

### A practical engineering scenario

A member enters on mobile, returns on web, and has only some account connections verified. The application should preserve their canonical profile and show which experience is available next, without inventing eligibility or reward state.

The design challenge spans authentication continuity, platform-specific navigation and honest projections of services that may be incomplete or unavailable.

### Client and authority boundaries

```mermaid
flowchart TD
    W["Next.js web client"] --> A["Application API"]
    M["React Native and Expo client"] --> A
    A --> O["Oracle identity and intelligence"]
    A --> Q["Q campaign and economic state"]
    O --> P["Profile and connection projections"]
    Q --> C["Campaign and receipt projections"]
```

This illustrates intended authority boundaries. It does not certify that every client-to-service path is integrated or deployed.

### Decisions and tradeoffs

| Decision | Why it matters | Cost to manage |
| --- | --- | --- |
| Share service contracts, retain distinct clients | Identity can remain consistent across devices | Web and native require separate validation |
| Present Oracle and Q state | The app avoids duplicating permanent identity and campaign authority | Service outages need clear interface states |
| Use platform-appropriate navigation | Mobile and desktop can fit their own interaction patterns | Design parity needs visual and behavioral review |

### Product direction

| Experience | Role |
| --- | --- |
| Universal Profile | Present persistent identity, connection state and reputation |
| Oracle | Make intelligence and assistance available across the application |
| Campaigns and rewards | Present Q participation, progress and economic receipts |
| Ecosystem discovery | Connect contribution, community and other product experiences |
| Multiple clients | Share identity and service contracts across web and mobile |

Oracle remains the authority for identity and reputation. Q remains the campaign/economic authority. Universe presents their state rather than creating a competing source of truth.

### Architecture direction

The approved client architecture uses Next.js for web/desktop and React Native with Expo for native mobile. Clients are intended to share API contracts, validation, identity types and design foundations while using platform-appropriate interfaces.

The native mobile direction includes iOS and Android clients. This is architectural intent, not a claim of App Store or Google Play availability.

### Engineering priorities

- Preserve account and contribution continuity across clients.
- Reuse backend services rather than duplicate business logic per interface.
- Keep privileged credentials out of client applications.
- Present partial connections, unavailable services and recovery steps clearly.
- Give desktop and native mobile their own appropriate interaction design.

### Current stage

Active application development and integration. The default branch contains separate Next.js web, Express/TypeScript API and React Native/Expo mobile packages, alongside home/native architecture specifications and mobile preview/visual-QA workflows.

Package presence and workflow definitions demonstrate build scope. Shared identity, intelligence and campaign journeys still require end-to-end verification.

Representative manifest review confirms Next.js/React for web and React Native/Expo for mobile. A shared-package extraction remains architecture direction rather than a completed monorepo claim.

This page does not certify deployment, store release or feature completeness.



## Development ownership

**Lead developer:** [Thomas Phillips](https://github.com/darealrektrush)  
**Collaborative developers:** [Thomas Phillips](https://github.com/darealrektrush) and [Andrew](https://github.com/Andrew-07)

This work combines product and architecture decisions, iterative implementation, integration review, verification and operational tradeoffs. Collaborative credit identifies shared development without equating authorship of distinct systems.

## Current evidence boundary

Ongoing web, API and React Native/Expo development, with Figma screen/layout work in progress. Shared service journeys require explicit end-to-end verification; the project is not represented as a released app.

The private implementation repository is [crabstar-universe](https://github.com/CrabStar-Ecosystem/crabstar-universe). Code, working prototypes, test results, deployed services, actual settlements and released product availability are distinct kinds of evidence.

## Publication boundary

This page intentionally excludes secrets, sensitive system details, private participant records, strategy parameters and transaction authorization configuration.
