"""Inactive install plan for the corrected SA4 v2 postcheck lineage."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).parents[2]


@dataclass(frozen=True)
class Change:
    source: str
    destination: str
    after_sha256: str
    owner: str = "root"
    group: str = "root"
    mode: str = "0644"
    operation: str = "create-exclusive"


def change(name: str, digest: str) -> Change:
    return Change(f"scripts/aster-adaptive/{name}",
                  f"/usr/local/libexec/aster-sa4/{name}", digest)


CHANGES = (
    change("sa4_canary_v2_target_bytes_check_v1.py",
           "74ee440c6f7617c726c634fd79ccfaf0e5d3df77cba4ba1b0aafcb78a64b0e06"),
    change("sa4_canary_v2_target_metadata_check_v1.py",
           "23fb5ac611c0e7e04ab672c0ab17eb86c92e4a9c9e334b6879d56066ae395fea"),
    change("sa4_canary_v2_consumer_health_check_v1.py",
           "4b792ff436a605a699dac3b73d4eb319b22ca4302ccf83ad3904379ba7fb4b28"),
    change("sa4_target_registry_v3.py",
           "35e7f680a10d4936ba246cd51e844d9cacbf47c6bda018ab27a88295ad304857"),
    change("sa4_distinct_postcheck_receipt_producer_v1.py",
           "96fa810011429f8da9fc1208a60471d745c452ed1ea9186552abf1ac4edeab29"),
    change("sa4_distinct_registry_bindings_v2.py",
           "b40a9b657cb3f1b9087d5621fb96e11735bb578c06bbfdea3fd342cdd8baa370"),
    change("sa4_root_transaction_owner_v6.py",
           "74ebd4e13137646dfff7a608bb3a9bb77050639968eaac321a15e7fb126dbd6f"),
    change("sa4_fixed_transaction_runner_v7.py",
           "8b3f030b06d2cb677a5a106ee3a4a8f4ca27360ad19403bd927dc672dd7c322d"),
)
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")
FRESH_PATHS = (
    "/var/lib/aster/sa4/transaction-input-v4",
    "/var/lib/aster/sa4/transaction-evidence-v4",
    "/var/lib/aster/sa4/one-use-ledger-v4",
)


def validate() -> None:
    if len(CHANGES) != 8 or len({item.destination for item in CHANGES}) != 8:
        raise ValueError("SA4 postcheck lineage correction set changed")
    for item in CHANGES:
        if hashlib.sha256((ROOT / item.source).read_bytes()).hexdigest() != item.after_sha256:
            raise ValueError("SA4 postcheck lineage correction source changed")
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith("/usr/local/libexec/aster-sa4/")
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")):
            raise ValueError("unsafe SA4 postcheck lineage installation")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-postcheck-lineage-inactive-install-plan.v1",
        "host": "lxc104", "changes": [asdict(item) for item in CHANGES],
        "target_sha256": TARGET_SHA256, "fresh_paths": list(FRESH_PATHS),
        "precondition": [
            "all-eight-destinations-absent", "installed-v5-v6-exact",
            "retained-v2-and-v3-attempts-exact", "all-v4-paths-absent",
            "target-restored-to-drifted-digest", "lease-ready",
            "runtime-controls-absent", "production-healthy",
        ],
        "postcheck": [
            "exact-root-owned-single-link-files", "isolated-imports",
            "v2-checks-pass-only-healthy-v2-artifact",
            "registry-v3-pins-v2-check-programs",
            "complete-observer-binding-and-restoration",
            "runner-rejects-arguments-before-v4-input",
            "retained-attempts-unchanged", "fresh-v4-state-absent",
            "target-unchanged", "production-healthy",
        ],
        "rollback": {
            "remove-only-exact-after-hashes": [
                item.destination for item in reversed(CHANGES)],
            "uncertainty": "retain-and-stop",
        },
        "effect_authorized": False, "automatic_routing": "off",
        "exclusions": [
            "no-runner-attempt", "no-signer", "no-authority",
            "no-ledger-claim", "no-checkpoint", "no-repair",
            "no-service-action", "no-route-or-promotion",
        ],
    }


validate()
