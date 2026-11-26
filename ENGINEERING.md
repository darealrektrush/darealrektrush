# Engineering you can inspect

[Back to the portfolio](README.md)

The portfolio spans persistent identity, campaign economics, on-chain research and applications across web and native mobile. This guide connects the product ambition to concrete design concerns and public evidence.

## Choose a route

| Interest | Start with | What you can inspect |
| --- | --- | --- |
| End-to-end product ownership | [Oracle case study](https://github.com/darealrektrush/oracle-product-case-study) | Historical interface examples, service architecture and engineering decisions |
| Campaign and economic systems | [Project Q](case-studies/project-q.md) | Identity authority, partial outcomes and calculation/settlement boundaries |
| AI and Solana research | [Shadow](case-studies/shadow.md) | Evidence quality, research reproducibility and staged execution boundaries |
| Applications across devices | [Universe](case-studies/universe.md) | Web/native clients and shared-service authority |
| Executable engineering | [Event Reconciliation Lab](examples/event-reconciliation/README.md) | See why a request stays pending, a confirmation stays unmatched, or the two reconcile. Includes seven tests. |
| Canonical identity claims | [Universal Profile Reconciliation Lab](examples/identity-reconciliation/README.md) | Trace a pending claim, a verified link and a conflicting owner across 12 tests. |

## Run the public examples

From the repository root, with Python 3.12 or newer:

```bash
python examples/event-reconciliation/reconcile.py
python -m unittest discover -s examples/event-reconciliation -p 'test_*.py' -v
python examples/identity-reconciliation/reconcile.py
python -m unittest discover -s examples/identity-reconciliation -p 'test_*.py' -v
python scripts/check_portfolio.py
```

The lab demonstrates duplicate handling, conflicting-event rejection and order-independent reconciliation over a finite batch. Its tests exercise pending observations and unmatched confirmations as well as reconciled results. The demo checks all 120 permutations of its five synthetic inputs.

Both examples use only synthetic records and the Python standard library. Neither implements production payment logic, chain-finality verification, OAuth or wallet ownership proofs, persistent identity merges or concurrent exactly-once effects.

## What the checks establish

The [portfolio workflow](https://github.com/darealrektrush/darealrektrush/actions/workflows/portfolio-checks.yml) runs both labs' tests and demos, validates relative file links in Markdown/HTML, parses the SVG assets and rejects links to the known private implementation repositories. It runs without repository secrets and has read-only contents permission.

Those checks protect the public example and navigation. They do not validate external websites, deployed CrabStar services, research performance or complete production security. Public repository visibility is reviewed separately from local file checks.

## Stage is part of the evidence

| Project | Evidence represented here | Next level of proof |
| --- | --- | --- |
| Oracle | Private source review and historical product interfaces | Fresh verification of expanded identity and cross-product journeys |
| Project Q | Campaign/economic components and selected test-source review | Hosted qualification of participant, contribution and receipt paths |
| Shadow | Research infrastructure, paper components and selected safety-test source | Integrated research verification and separately qualified execution |
| Universe | Web/API/native packages and architecture specifications | Verified shared-service journeys across clients |

Implementation, automated tests, deployment and a verified user journey are distinct milestones. These descriptions are a review snapshot, not release or availability promises.

## Public evidence, protected implementation

Public material shows problems, responsibilities, tradeoffs, sanitized product examples and runnable educational code. Production source, privileged protocols, strategy parameters, private user records and unreleased commercial terms remain outside these showcases.

Credentials never belong in source control, including private repositories.
