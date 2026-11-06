"""Accepted SA4 registry with the v2 canary's own postcheck lineage."""
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
            "74ee440c6f7617c726c634fd79ccfaf0e5d3df77cba4ba1b0aafcb78a64b0e06",
            "23fb5ac611c0e7e04ab672c0ab17eb86c92e4a9c9e334b6879d56066ae395fea",
            "4b792ff436a605a699dac3b73d4eb319b22ca4302ccf83ad3904379ba7fb4b28"),
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
