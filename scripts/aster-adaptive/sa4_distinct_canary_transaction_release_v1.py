"""No-authority source release for the distinct SA4 v2 canary chain."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sa4_distinct_canary_seed_inactive_install_result_v1 as seed_result
import sa4_target_registry_v2 as registry


ROOT = Path(__file__).parents[2]
TARGET_ID = "sa4-lxc104-canary-adapter-v2"
TARGET_BEFORE_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")
TARGET_AFTER_SHA256 = (
    "fae178a1558199b66f4dc9abec18690ed22a7cbee398f411b47f93daf1d3a0c2")
SEED_RESULT = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-distinct-canary-v2-seed-install-result-2026-11-06.json")
SEED_RESULT_SHA256 = (
    "299553312a2c247a87aec8a70925cf08a45553da101e5d4bd2a2cab9ccf78e38")
SOURCES = {
    "scripts/aster-adaptive/sa4_target_registry_v2.py":
        "86c442725544480c85c6bdb5507c17d48acc16e58994e32fffaae944f696da39",
    "scripts/aster-adaptive/sa4_root_transaction_owner_v3.py":
        "2b2d08249072c52dd5e2f79ff3f525bdb46c647a79225993e964dd6e7dd49fb0",
    "scripts/aster-adaptive/sa4_fixed_transaction_runner_v3.py":
        "9c6bfbbe05dfa6d574988df3a99b79696fcfee1353d24461324806df2ec0cc9f",
}


def validate_static_evidence() -> None:
    for path, expected in SOURCES.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("SA4 distinct-canary transaction source changed")
    raw = SEED_RESULT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SEED_RESULT_SHA256:
        raise ValueError("SA4 distinct-canary seed result changed")
    if seed_result.validate(raw)["inactive"] is not True:
        raise ValueError("SA4 distinct-canary seed is not inactive")
    target = registry.resolve_production(TARGET_ID)
    if target.host_id != "lxc104" or target.path != (
            "/var/lib/aster/sa4/canary-adapter-v2.json"):
        raise ValueError("SA4 distinct-canary target changed")


def packet() -> dict[str, object]:
    validate_static_evidence()
    return {
        "schema": "aster-sa4-distinct-canary-transaction-release.v1",
        "release_id": "sa4-canary-v2-first-transaction-source-v1",
        "target_id": TARGET_ID,
        "target_before_sha256": TARGET_BEFORE_SHA256,
        "target_after_sha256": TARGET_AFTER_SHA256,
        "seed_install_result_sha256": SEED_RESULT_SHA256,
        "source_sha256": dict(SOURCES),
        "runtime_paths": {
            "input": "/var/lib/aster/sa4/transaction-input-v2",
            "evidence": "/var/lib/aster/sa4/transaction-evidence-v2",
            "ledger": "/var/lib/aster/sa4/one-use-ledger-v2",
            "operation_id": "sa4-canary-v2-first-operation-v1",
        },
        "transaction_limits": {
            "maximum_repairs": 1, "maximum_rollbacks": 1,
            "automatic_retry": False, "service_restart": False,
            "automatic_routing": "off",
        },
        "status": "source-complete-pending-inactive-install-review",
        "effect_authorized": False,
        "exclusions": [
            "no-authority", "no-signature", "no-ledger-claim",
            "no-checkpoint", "no-repair", "no-service-action",
            "no-route", "no-promotion",
        ],
    }


def canonical_packet() -> bytes:
    return (json.dumps(packet(), sort_keys=True, separators=(",", ":"))
            + "\n").encode()


def packet_sha256() -> str:
    return hashlib.sha256(canonical_packet()).hexdigest()


validate_static_evidence()

