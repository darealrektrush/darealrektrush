# Event Reconciliation Lab

**Runnable engineering example · Synthetic data · Python standard library**

A small, inspectable demonstration of handling repeated and out-of-order events. It illustrates reliability concerns relevant to connected products without reproducing Oracle, Q or Shadow implementation.

## Run it

Use Python 3.10 or later. No installation, credentials or network access are needed.

```bash
cd examples/event-reconciliation
python3 reconcile.py
python3 -m unittest -v
```

Expected demo output:

```text
synthetic-A: reconciled
synthetic-B: pending
synthetic-C: unmatched_confirmation
Accepted events: 4; duplicates: 1
All 120 delivery permutations produce the same result.
```

## What to inspect

| Input condition | Result |
| --- | --- |
| Same event delivered again | Counted as a duplicate; operation state is unchanged |
| One event identifier reused for different content | Reject the complete batch |
| Confirmation arrives before request | Both observations reconcile regardless of order |
| Confirmation has no matching request | Explicit unmatched state |
| Request has no confirmation | Pending state |
| Unsupported or malformed event | Reject the batch |

The function validates and deduplicates the complete batch before deriving a sorted, deterministic snapshot. Seven tests cover replay, all 24 orders of a four-event batch, conflicts, missing requests, invalid input and empty batches. The demo also checks all 120 permutations of its five-event input.

## Deliberate scope

This is a new educational example, not extracted production code. “Reconciled” means two synthetic observations share an operation identifier; it does not establish authorization, payment, blockchain finality or authenticity.

The model runs in memory on a complete batch. It does not persist events, handle concurrent workers, implement transport retries or prove exactly-once external effects. A real service would also need authenticated evidence, durable uniqueness constraints, transactional boundaries, monitoring and recovery appropriate to its domain.

[Back to the portfolio](../../README.md)
