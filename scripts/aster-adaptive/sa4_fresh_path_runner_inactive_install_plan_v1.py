"""Inactive install plan for the fresh-path SA4 v6 runner."""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).parents[2]
SOURCE = "scripts/aster-adaptive/sa4_fixed_transaction_runner_v6.py"
DESTINATION = "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v6.py"
AFTER_SHA256 = (
    "a91d6a34ac251970a9d83452e085cbc4d0a51adaf065ec75d6879e122b38a397")
V5 = {
    "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v5.py":
        "a4fd70730a9e752e12430c1ab2179eb0c876118ab839c946850dd3377df6167a",
    "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v5.py":
        "1071e4aa857e9ad1b6f3fa53de2ea22500919f278906f9b997f2ace1579c7b6f",
}
RETAINED_PATHS = (
    "/var/lib/aster/sa4/transaction-input-v2",
    "/var/lib/aster/sa4/transaction-evidence-v2",
)
FRESH_PATHS = (
    "/var/lib/aster/sa4/transaction-input-v3",
    "/var/lib/aster/sa4/transaction-evidence-v3",
    "/var/lib/aster/sa4/one-use-ledger-v3",
)


def validate() -> None:
    if hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest() != AFTER_SHA256:
        raise ValueError("SA4 v6 runner source changed")
    if (str(PurePosixPath(DESTINATION)) != DESTINATION
            or not DESTINATION.startswith("/usr/local/libexec/aster-sa4/")):
        raise ValueError("unsafe SA4 v6 runner destination")
    if len(set((*RETAINED_PATHS, *FRESH_PATHS))) != 5:
        raise ValueError("SA4 v6 transaction paths overlap")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-fresh-path-runner-inactive-install-plan.v1",
        "host": "lxc104",
        "change": {
            "source": SOURCE, "destination": DESTINATION,
            "after_sha256": AFTER_SHA256, "owner": "root", "group": "root",
            "mode": "0644", "operation": "create-exclusive",
        },
        "installed_v5": dict(V5),
        "retained_failed_paths": list(RETAINED_PATHS),
        "fresh_paths": list(FRESH_PATHS),
        "precondition": [
            "destination-absent", "exact-v5-interface-correction",
            "retained-v2-attempt-exact", "all-v3-runtime-paths-absent",
            "target-still-drifted", "lease-ready", "production-healthy",
        ],
        "postcheck": [
            "exact-root-owned-single-link-file", "isolated-import",
            "fresh-path-binding-and-restoration", "target-interface-exact",
            "argument-rejected-before-v3-input", "retained-v2-unchanged",
            "fresh-v3-state-absent", "target-unchanged", "production-healthy",
        ],
        "rollback": {
            "remove-only-if-exact-after-sha256": DESTINATION,
            "uncertainty": "retain-and-stop",
        },
        "effect_authorized": False,
        "automatic_routing": "off",
        "exclusions": [
            "no-runner-attempt", "no-signer", "no-authority",
            "no-ledger-claim", "no-checkpoint", "no-repair",
            "no-service-action", "no-route-or-promotion",
        ],
    }


validate()
