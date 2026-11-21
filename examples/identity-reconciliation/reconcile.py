"""Offline canonical-profile claim reconciliation using invented identities only.

Educational model: proof_verified is a caller-supplied fixture, NOT proof verification.
No network calls, persistent storage, account merging, or production Oracle code.
"""
from dataclasses import dataclass


KINDS = frozenset({"telegram", "x", "google", "apple", "solana_wallet"})


@dataclass(frozen=True)
class Profile:
    profile_id: str
    lifetime_xp: int


@dataclass(frozen=True)
class Claim:
    event_id: str
    profile_id: str
    kind: str
    subject: str
    proof_verified: bool


@dataclass(frozen=True)
class Snapshot:
    profiles: tuple[tuple[str, int], ...]
    connections: tuple[tuple[str, str, str], ...]
    pending: tuple[str, ...]
    duplicates: int


def reconcile(profiles: list[Profile], claims: list[Claim]) -> Snapshot:
    """Compute a deterministic snapshot; reject ambiguous/conflicting batches.

    All validation occurs before deriving a result. No unproven claim creates
    ownership, and nothing can automatically merge two canonical profiles.
    """
    profile_map: dict[str, int] = {}
    for profile in profiles:
        if (not isinstance(profile, Profile)
                or not isinstance(profile.profile_id, str)
                or not profile.profile_id.strip()
                or type(profile.lifetime_xp) is not int
                or profile.lifetime_xp < 0):
            raise ValueError("Invalid canonical profile")
        if profile.profile_id in profile_map:
            raise ValueError("Duplicate canonical profile ID")
        profile_map[profile.profile_id] = profile.lifetime_xp

    events: dict[str, Claim] = {}
    duplicates = 0
    for claim in claims:
        if not isinstance(claim, Claim):
            raise ValueError("Expected Claim")
        if (not isinstance(claim.event_id, str) or not claim.event_id.strip()
                or not isinstance(claim.profile_id, str) or not claim.profile_id.strip()
                or not isinstance(claim.subject, str) or not claim.subject.strip()
                or claim.kind not in KINDS
                or type(claim.proof_verified) is not bool):
            raise ValueError("Malformed claim")
        if claim.profile_id not in profile_map:
            raise ValueError("Unknown canonical profile")
        previous = events.get(claim.event_id)
        if previous is not None:
            if previous != claim:
                raise ValueError("Conflicting event ID")
            duplicates += 1
        else:
            events[claim.event_id] = claim

    # A supplied verification boolean represents an upstream proof decision.
    # Unverified events are pending, and never establish ownership.
    pending = tuple(sorted(event.event_id for event in events.values()
                           if not event.proof_verified))
    ownership: dict[tuple[str, str], str] = {}
    connections: set[tuple[str, str, str]] = set()
    for claim in events.values():
        if not claim.proof_verified:
            continue
        key = (claim.kind, claim.subject)
        owner = ownership.get(key)
        if owner is not None and owner != claim.profile_id:
            raise ValueError("Conflicting verified ownership; manual review required")
        ownership[key] = claim.profile_id
        connections.add((claim.profile_id, claim.kind, claim.subject))

    return Snapshot(
        profiles=tuple(sorted(profile_map.items())),
        connections=tuple(sorted(connections)),
        pending=pending,
        duplicates=duplicates,
    )


def demo() -> None:
    profiles = [Profile("member-A", 1250), Profile("member-B", 90)]
    claims = [
        Claim("claim-01", "member-A", "telegram", "tg-user-100", True),
        Claim("claim-02", "member-A", "google", "google-sub-500", True),
        Claim("claim-03", "member-A", "solana_wallet", "synthetic-wallet-X", False),
        Claim("claim-01", "member-A", "telegram", "tg-user-100", True),
    ]
    result = reconcile(profiles, claims)
    for profile_id, xp in result.profiles:
        print(f"{profile_id}: retained lifetime XP {xp}")
    for profile_id, kind, _ in result.connections:
        print(f"{profile_id}: linked verified {kind}")
    print(f"Pending proofs: {len(result.pending)}; duplicate deliveries: {result.duplicates}")
    assert result.profiles == (("member-A", 1250), ("member-B", 90))
    assert len(result.connections) == 2 and result.pending == ("claim-03",)


if __name__ == "__main__":
    demo()
