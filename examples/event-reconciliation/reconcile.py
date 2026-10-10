"""Synthetic, offline event reconciliation. No production integrations."""
from dataclasses import dataclass
from itertools import permutations


@dataclass(frozen=True)
class Event:
    event_id: str
    operation_id: str
    stage: str


@dataclass(frozen=True)
class Result:
    operations: tuple[tuple[str, str], ...]
    accepted_events: int
    duplicates: int


STAGES = frozenset({"requested", "confirmed"})


def reconcile(events: list[Event]) -> Result:
    """Replay a complete batch; conflicting identifiers fail the whole batch."""
    unique: dict[str, Event] = {}
    duplicates = 0
    for event in events:
        if not isinstance(event, Event):
            raise ValueError("Expected an Event")
        if any(not isinstance(value, str) or not value.strip()
               for value in (event.event_id, event.operation_id, event.stage)):
            raise ValueError("Event fields must be nonempty strings")
        if event.stage not in STAGES:
            raise ValueError("Unsupported stage")
        previous = unique.get(event.event_id)
        if previous is not None:
            if previous != event:
                raise ValueError("Conflicting payload for event identifier")
            duplicates += 1
        else:
            unique[event.event_id] = event

    observed: dict[str, set[str]] = {}
    for event in unique.values():
        observed.setdefault(event.operation_id, set()).add(event.stage)

    operations = []
    for operation_id, stages in sorted(observed.items()):
        if stages == STAGES:
            status = "reconciled"
        elif "confirmed" in stages:
            status = "unmatched_confirmation"
        else:
            status = "pending"
        operations.append((operation_id, status))
    return Result(tuple(operations), len(unique), duplicates)


def demo() -> None:
    events = [
        Event("evt-02", "synthetic-A", "confirmed"),
        Event("evt-01", "synthetic-A", "requested"),
        Event("evt-01", "synthetic-A", "requested"),
        Event("evt-03", "synthetic-B", "requested"),
        Event("evt-04", "synthetic-C", "confirmed"),
    ]
    result = reconcile(events)
    assert all(reconcile(list(order)) == result for order in permutations(events))
    for operation_id, status in result.operations:
        print(f"{operation_id}: {status}")
    print(f"Accepted events: {result.accepted_events}; duplicates: {result.duplicates}")
    print("All 120 delivery permutations produce the same result.")


if __name__ == "__main__":
    demo()
