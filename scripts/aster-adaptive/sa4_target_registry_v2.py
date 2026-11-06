"""Accepted SA4 target registry including the distinct inert v2 canary.

This source grants no effect authority.  Until separately installed and used
by a separately reviewed transaction chain it changes no live resolver.
"""
from __future__ import annotations

import sa4_target_registry_v1 as previous
from sa4_target_registry_v1 import Target


SCHEMA_FIXTURES = previous.SCHEMA_FIXTURES
PRODUCTION_TARGETS = previous.PRODUCTION_TARGETS + (
    Target(
        target_id="sa4-lxc104-canary-adapter-v2",
        host_id="lxc104",
        path="/var/lib/aster/sa4/canary-adapter-v2.json",
        owner="root", group="root", mode="0644",
        classification="low-criticality-read-only-adapter",
        checkpoint_parent="/var/lib/aster/sa4/checkpoints",
        temporary_path="/var/lib/aster/sa4/.canary-adapter-v2.json.sa4-tmp",
        maximum_bytes=4096,
        postcheck_ids=(
            "target-bytes", "target-metadata", "consumer-read-only-health"),
        postcheck_program_sha256=(
            "f8f544ca04b7587b76d827ea1e193c56bb814a231b498c6652009e098bdd00a1",
            "e61bb89bd366e03fed0bafaa23b18db484f1b2a6133b2a708469b9b66d49a041",
            "1214189f36c4bb75a90028cd31c15f4dd5ecf6977582ada67cd72a5ce65c72da"),
        rollback_program_sha256=
            "15f924f589980d786e7d0f8ad5ac5f03e32e95d907737a6c2d4ae9adad61ffdb",
        owner_review_sha256=
            "53070fd50f53ae288d44d3c5e67892090a08387d510a1cd6731cb84102871422"),
)


def registration_document(item: Target) -> dict[str, object]:
    return previous.registration_document(item)


def registration_sha256(item: Target) -> str:
    return previous.registration_sha256(item)


def resolve_production(target_id: str) -> Target:
    return previous._resolve(PRODUCTION_TARGETS, target_id, synthetic=False)


def resolve_schema_fixture(target_id: str) -> Target:
    return previous._resolve(SCHEMA_FIXTURES, target_id, synthetic=True)


previous.validate_registry(PRODUCTION_TARGETS, synthetic=False)
