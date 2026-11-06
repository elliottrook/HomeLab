"""Inactive install plan for the SA4 runner/owner interface correction."""
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


CHANGES = (
    Change(
        "scripts/aster-adaptive/sa4_root_transaction_owner_v5.py",
        "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v5.py",
        "a4fd70730a9e752e12430c1ab2179eb0c876118ab839c946850dd3377df6167a"),
    Change(
        "scripts/aster-adaptive/sa4_fixed_transaction_runner_v5.py",
        "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v5.py",
        "1071e4aa857e9ad1b6f3fa53de2ea22500919f278906f9b997f2ace1579c7b6f"),
)
PREDECESSOR = {
    "/usr/local/libexec/aster-sa4/sa4_distinct_registry_bindings_v1.py":
        "c88640a32fb9a413afcd01e2dcdadcb4a5fc68f0bdd99a59e976aa5f83476330",
    "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v4.py":
        "9da52be5fba3d9a5c628e94a887f034944d6a75f31bf8dbb86471005ff5453e6",
    "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v4.py":
        "ab2c67cd1640cbb60b3da89aadc9f90ee34132873295f8736f10ed0af3b79d0f",
}
TARGET_PATH = "/var/lib/aster/sa4/canary-adapter-v2.json"
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")
FAILED_ATTEMPT = {
    "runner": "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v4.py",
    "exit_status": 1,
    "failure_class": "deterministic-source-interface-defect",
    "failure_code": "missing-root-owner-bound-target-id",
    "repair_attempted": False,
    "grant_claimed": False,
}


def validate() -> None:
    if len(CHANGES) != 2 or len({item.destination for item in CHANGES}) != 2:
        raise ValueError("SA4 runner interface correction set changed")
    for item in CHANGES:
        if hashlib.sha256((ROOT / item.source).read_bytes()).hexdigest() != item.after_sha256:
            raise ValueError("SA4 runner interface correction source changed")
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith("/usr/local/libexec/aster-sa4/")
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")):
            raise ValueError("unsafe SA4 runner interface correction install")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-runner-interface-fix-inactive-install-plan.v1",
        "host": "lxc104",
        "changes": [asdict(item) for item in CHANGES],
        "predecessor": dict(PREDECESSOR),
        "failed_attempt": dict(FAILED_ATTEMPT),
        "target": {"path": TARGET_PATH, "sha256": TARGET_SHA256},
        "precondition": [
            "both-v5-destinations-absent", "exact-v4-predecessor",
            "exact-drifted-v2-canary", "failed-input-and-evidence-retained",
            "one-use-ledger-absent", "runtime-controls-absent",
            "lease-ready", "production-healthy",
        ],
        "postcheck": [
            "exact-root-owned-single-link-files", "isolated-imports-only",
            "v5-owner-exposes-fixed-bound-target-interface",
            "v5-runner-rejects-arguments-before-input",
            "retained-failed-attempt-unchanged", "target-unchanged",
            "production-healthy",
        ],
        "rollback": {
            "remove-only-exact-after-hashes": [
                item.destination for item in reversed(CHANGES)],
            "uncertainty": "retain-and-stop",
        },
        "effect_authorized": False,
        "automatic_routing": "off",
        "exclusions": [
            "no-runner-invocation", "no-signer", "no-new-authority",
            "no-ledger-claim", "no-checkpoint", "no-repair",
            "no-service-action", "no-route-or-promotion",
        ],
    }


validate()
