import unittest
from itertools import permutations

from reconcile import Event, Result, reconcile


class ReconciliationTests(unittest.TestCase):
    def test_duplicate_replay_does_not_add_operations(self):
        events = [Event("r1", "A", "requested"), Event("c1", "A", "confirmed")]
        once = reconcile(events)
        replayed = reconcile(events + events)
        self.assertEqual(replayed.operations, once.operations)
        self.assertEqual(replayed.accepted_events, 2)
        self.assertEqual(replayed.duplicates, 2)

    def test_all_delivery_orders_converge(self):
        events = [
            Event("c1", "A", "confirmed"), Event("r1", "A", "requested"),
            Event("r2", "B", "requested"), Event("c2", "C", "confirmed"),
        ]
        expected = Result(
            (("A", "reconciled"), ("B", "pending"), ("C", "unmatched_confirmation")),
            4, 0,
        )
        for order in permutations(events):
            self.assertEqual(reconcile(list(order)), expected)

    def test_conflicting_identifier_fails_in_either_order(self):
        conflicts = [
            Event("same", "A", "requested"),
            Event("same", "B", "requested"),
        ]
        for order in permutations(conflicts):
            with self.assertRaisesRegex(ValueError, "Conflicting"):
                reconcile(list(order))

    def test_conflicting_stage_also_fails(self):
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            reconcile([Event("same", "A", "requested"), Event("same", "A", "confirmed")])

    def test_unmatched_confirmation_is_not_reconciled(self):
        self.assertEqual(
            reconcile([Event("c1", "A", "confirmed")]).operations,
            (("A", "unmatched_confirmation"),),
        )

    def test_invalid_input_is_rejected(self):
        invalid = [
            Event("", "A", "requested"), Event("x", " ", "requested"),
            Event("x", "A", "unknown"), Event("x", "A", 3), None,
        ]
        for event in invalid:
            with self.subTest(event=event), self.assertRaises(ValueError):
                reconcile([event])

    def test_empty_batch(self):
        self.assertEqual(reconcile([]), Result((), 0, 0))


if __name__ == "__main__":
    unittest.main()
