"""Inactive install plan for the corrected SA4 v2 terminal chain."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


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
        "scripts/aster-adaptive/sa4_receipt_ledger_reconciler_v2.py",
        "/usr/local/libexec/aster-sa4/sa4_receipt_ledger_reconciler_v2.py",
        "9889f6436c645be9fa735cb7428cc95e717ead87dc82b2f0a2b1b08c06abf41e"),
    Change(
        "scripts/aster-adaptive/sa4_root_transaction_owner_v2.py",
        "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v2.py",
        "a97645ae5365c1121d6acc9ed778bb769f442bb964b21a2687d46443ba7269bc"),
    Change(
        "scripts/aster-adaptive/sa4_one_shot_transaction_controller_v2.py",
        "/usr/local/libexec/aster-sa4/sa4_one_shot_transaction_controller_v2.py",
        "10d98960957d8226830720cd8c280de0d4b67108a5ae96dc41cce78f7a83daf3"),
    Change(
        "scripts/aster-adaptive/sa4_fixed_transaction_runner_v2.py",
        "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v2.py",
        "752f1f41f6382b91e29cc210d84bd6955fd54f247c612bde2eb6347810e61883"),
)

INSTALLED_V1_DEPENDENCIES = {
    "/usr/local/libexec/aster-sa4/sa4_runtime_control_owner_v1.py":
        "6d6e89d22829395373089c50eece2ffcdcc042c70c85a25a2f38867f2b330daa",
    "/usr/local/libexec/aster-sa4/sa4_observer_file_exchange_v1.py":
        "6cddfd315ca70753e7065de7d01eb176f9fc4b0a0d4740d326f3d08be1883a63",
}


def validate() -> None:
    if len(CHANGES) != 4 or len({item.destination for item in CHANGES}) != 4:
        raise ValueError("SA4 v2 inactive install set changed")
    for item in CHANGES:
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith(
                    "/usr/local/libexec/aster-sa4/")
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")):
            raise ValueError("unsafe SA4 v2 inactive install")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-terminal-reconciliation-v2-inactive-install-plan.v1",
        "host": "lxc104",
        "changes": [asdict(item) for item in CHANGES],
        "installed_v1_dependencies": INSTALLED_V1_DEPENDENCIES,
        "precondition": [
            "all-v2-destinations-absent", "exact-v1-dependencies",
            "lease-ready", "operation-lock-absent", "emergency-stop-absent",
            "transaction-input-and-evidence-retained", "production-healthy"],
        "postcheck": [
            "exact-root-owned-single-link-files", "isolated-imports-only",
            "no-v2-runner-invocation", "no-authority-or-target-touch",
            "runtime-state-unchanged", "production-healthy"],
        "rollback": {
            "remove-only-exact-after-hashes": [
                item.destination for item in reversed(CHANGES)],
            "uncertainty": "retain-and-stop"},
        "effect_authorized": False,
        "automatic_routing": "off",
        "exclusions": [
            "no-signer", "no-grant", "no-ledger-rewrite", "no-repair",
            "no-service-action", "no-route-or-promotion"],
    }


validate()
