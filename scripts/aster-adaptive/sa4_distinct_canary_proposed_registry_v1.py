"""Source-only proposed registry for a second inert SA4 canary.

This module is deliberately separate from the production target registry.  It
can validate and describe the proposal, but no installed repair component
imports it and it grants no production resolution or effect authority.
"""
from __future__ import annotations

from sa4_target_registry_v1 import (
    Target, _resolve, registration_document, registration_sha256,
    validate_registry)


PROPOSED_TARGETS = (
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
            "6934128f34abfae5ef43de6dc751b1d70865964a3f0a3119fb89bd2f72aea713"),
)


def resolve_proposed(target_id: str) -> Target:
    return _resolve(PROPOSED_TARGETS, target_id, synthetic=False)


validate_registry(PROPOSED_TARGETS, synthetic=False)
