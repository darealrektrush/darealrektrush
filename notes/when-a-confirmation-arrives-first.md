# When a confirmation arrives first

*Thomas Phillips*

A confirmation arrives. A moment later the request arrives, followed by a second copy of that request. If each arrival overwrites a status field, the operation ends up marked “requested.” The consumer has already seen the confirmation. It has even stored it once. The latest write erased the evidence it needed.

I put that sequence in a small Python lab. The input has three fields. The event ID identifies an observation, such as a request. The operation ID connects observations about the same piece of work. The stage says what was observed. Keeping both IDs matters. If I deduplicate on the operation ID, I risk discarding a legitimate confirmation. If I deduplicate on the event ID alone and never group the surviving events, I can count messages but can’t tell which operations have both observations.

Here is the complete input, in delivery order.

| Event ID | Operation | Stage |
|---|---|---|
| evt-02 | synthetic-A | confirmed |
| evt-01 | synthetic-A | requested |
| evt-01 | synthetic-A | requested |
| evt-03 | synthetic-B | requested |
| evt-04 | synthetic-C | confirmed |

The lab first builds a dictionary keyed by event ID. When a known ID carries the same fields, it counts a repeat. When a known ID carries different fields, it rejects the batch. Silently keeping whichever version arrived first would let delivery order determine which story survives.

The second pass groups the accepted stages by operation. A request and confirmation together reconcile A. The request for B stays pending. The confirmation for C stays visible as unmatched. That third result matters to someone investigating a discrepancy. They can look for C’s missing request without assuming the work either succeeded or failed.

## Try it

Use Git and Python 3.10 or newer. The pinned checkout below uses synthetic records and runs offline after cloning.

```bash
git clone https://github.com/darealrektrush/darealrektrush.git
cd darealrektrush
git checkout --detach cbef2c70fdc203d540157afe095ed35c662eeb26
cd examples/event-reconciliation
python3 reconcile.py
python3 -m unittest -v
```

The demo prints the following result.

```text
synthetic-A: reconciled
synthetic-B: pending
synthetic-C: unmatched_confirmation
Accepted events: 4; duplicates: 1
All 120 delivery permutations produce the same result.
```

Five input positions have 120 permutations. Two positions hold identical records, which leaves 60 distinct sequences of values. Every sequence produces the same operation states and counters. A separate unit test checks a different question. When one event ID is reused for two different operations, both arrival orders raise an error. Flipping their order can’t turn a conflict into an accepted batch. [Read the implementation](https://github.com/darealrektrush/darealrektrush/blob/cbef2c70fdc203d540157afe095ed35c662eeb26/examples/event-reconciliation/reconcile.py) · [Inspect the seven tests](https://github.com/darealrektrush/darealrektrush/blob/cbef2c70fdc203d540157afe095ed35c662eeb26/examples/event-reconciliation/test_reconcile.py)

For a quick experiment, remove the repeated request from the demo and rerun the reconciliation function on those four observations. The duplicate counter drops to zero and the operation states stay the same. Add a new request for C with a fresh event ID, and C reconciles. In one case you learned something about transport. In the other you learned something about the work.

This model has the whole batch in memory. A consumer that sends a notification or moves money has another question to answer: what happens if it crashes between performing the action and recording the result? A deterministic account of the input is useful evidence. Handling that crash requires a durable design for the side effect itself.
