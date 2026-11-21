"""Synthetic tests for the educational identity-claim reconciliation model."""
import unittest
from itertools import permutations

from reconcile import Claim, Profile, Snapshot, reconcile


PROFILES = [Profile("member-A", 1250), Profile("member-B", 90)]


class IdentityReconciliationTests(unittest.TestCase):
    def test_verified_claim_preserves_canonical_profile_history(self):
        result = reconcile(PROFILES, [Claim("e1", "member-A", "google", "google-1", True)])
        self.assertEqual(result.profiles, (("member-A", 1250), ("member-B", 90)))
        self.assertEqual(result.connections, (("member-A", "google", "google-1"),))

    def test_unverified_claim_never_establishes_ownership(self):
        result = reconcile(PROFILES, [Claim("e1", "member-A", "solana_wallet", "wallet-1", False)])
        self.assertEqual(result.connections, ())
        self.assertEqual(result.pending, ("e1",))

    def test_replayed_claim_does_not_duplicate_connection(self):
        event = Claim("e1", "member-A", "telegram", "tg-1", True)
        result = reconcile(PROFILES, [event, event])
        self.assertEqual(len(result.connections), 1)
        self.assertEqual(result.duplicates, 1)

    def test_conflicting_event_id_fails_closed(self):
        a = Claim("same", "member-A", "google", "google-1", True)
        b = Claim("same", "member-A", "google", "google-2", True)
        for order in permutations([a, b]):
            with self.assertRaisesRegex(ValueError, "Conflicting event ID"):
                reconcile(PROFILES, list(order))

    def test_verified_subject_cannot_be_claimed_by_two_profiles(self):
        a = Claim("e1", "member-A", "solana_wallet", "wallet-1", True)
        b = Claim("e2", "member-B", "solana_wallet", "wallet-1", True)
        for order in permutations([a, b]):
            with self.assertRaisesRegex(ValueError, "manual review"):
                reconcile(PROFILES, list(order))

    def test_unverified_competing_claim_does_not_override_verified_owner(self):
        claims = [Claim("e1", "member-A", "x", "x-user-1", True),
                  Claim("e2", "member-B", "x", "x-user-1", False)]
        result = reconcile(PROFILES, claims)
        self.assertEqual(result.connections, (("member-A", "x", "x-user-1"),))
        self.assertEqual(result.pending, ("e2",))

    def test_two_accounts_same_profile_never_creates_extra_identity(self):
        claims = [Claim("e1", "member-A", "telegram", "tg-1", True),
                  Claim("e2", "member-A", "apple", "apple-1", True)]
        result = reconcile(PROFILES, claims)
        self.assertEqual(len(result.profiles), 2)
        self.assertEqual(len(result.connections), 2)

    def test_delivery_order_does_not_change_snapshot(self):
        claims = [Claim("e1", "member-A", "telegram", "tg-1", True),
                  Claim("e2", "member-A", "google", "google-1", True),
                  Claim("e3", "member-B", "solana_wallet", "wallet-2", False),
                  Claim("e4", "member-B", "x", "x-2", True)]
        expected = reconcile(PROFILES, claims)
        for order in permutations(claims):
            self.assertEqual(reconcile(PROFILES, list(order)), expected)

    def test_missing_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            reconcile(PROFILES, [Claim("e1", "unknown", "google", "g1", True)])

    def test_invalid_inputs_rejected(self):
        invalid = [Claim("", "member-A", "google", "g", True),
                   Claim("e", "member-A", "unknown", "g", True),
                   Claim("e", "member-A", "google", "", True),
                   Claim("e", "member-A", "google", "g", 1), None]
        for claim in invalid:
            with self.subTest(claim=claim), self.assertRaises(ValueError):
                reconcile(PROFILES, [claim])

    def test_duplicate_or_invalid_seed_profile_rejected(self):
        for profiles in ([Profile("a", 1), Profile("a", 2)],
                         [Profile("", 1)],
                         [Profile("a", -1)],
                         [Profile("a", True)]):
            with self.subTest(profiles=profiles), self.assertRaises(ValueError):
                reconcile(profiles, [])

    def test_empty_claim_batch_keeps_profiles(self):
        self.assertEqual(reconcile(PROFILES, []), Snapshot(
            (("member-A", 1250), ("member-B", 90)), (), (), 0))


if __name__ == "__main__":
    unittest.main()
