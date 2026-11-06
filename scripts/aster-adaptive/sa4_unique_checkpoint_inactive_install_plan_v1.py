"""Create-exclusive install plan for SA4 preclaim reconciliation and v8."""
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
        "scripts/aster-adaptive/sa4_preclaim_failure_reconciler_v1.py",
        "/usr/local/libexec/aster-sa4/sa4_preclaim_failure_reconciler_v1.py",
        "dc3cc24e98550fbb8732dc89eaccfedb92ef980b5037d6e83939d027193a7a9c"),
    Change(
        "scripts/aster-adaptive/sa4_fixed_transaction_runner_v8.py",
        "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v8.py",
        "8be3e587c4bbc787f21a7f34ae3ab2abae31829faf8862d581303ce75bd5fea6"),
)


def validate() -> None:
    if len(CHANGES) != 2 or len({item.destination for item in CHANGES}) != 2:
        raise ValueError("SA4 unique-checkpoint install set changed")
    for item in CHANGES:
        if hashlib.sha256((ROOT / item.source).read_bytes()).hexdigest() != item.after_sha256:
            raise ValueError("SA4 unique-checkpoint install source changed")
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith("/usr/local/libexec/aster-sa4/")
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")):
            raise ValueError("unsafe SA4 unique-checkpoint installation")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-unique-checkpoint-inactive-install-plan.v1",
        "host": "lxc104", "changes": [asdict(item) for item in CHANGES],
        "precondition": [
            "both-destinations-absent", "installed-v7-exact",
            "v4-target-unchanged", "v4-ledger-ready-use-zero",
            "v4-evidence-empty", "v4-exchange-empty",
            "v4-runtime-controls-exact-and-unheld",
            "retained-colliding-checkpoint-exact", "lease-ready",
            "production-healthy",
        ],
        "postcheck": [
            "exact-root-owned-single-link-files",
            "reconciler-rejects-arguments-before-state",
            "v8-rejects-arguments-before-input", "v4-state-unchanged",
            "target-unchanged", "production-healthy",
        ],
        "rollback": {
            "remove-only-exact-after-hashes": [
                item.destination for item in reversed(CHANGES)],
            "uncertainty": "retain-and-stop",
        },
        "effect_authorized": False, "automatic_routing": "off",
        "exclusions": [
            "no-reconciler-invocation", "no-runner-attempt", "no-signer",
            "no-authority", "no-ledger-claim", "no-checkpoint",
            "no-repair", "no-service-action", "no-route-or-promotion",
        ],
    }


validate()
