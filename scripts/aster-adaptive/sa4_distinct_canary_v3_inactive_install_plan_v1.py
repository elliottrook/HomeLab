"""Reversible inactive install plan for the distinct-canary v3 chain."""
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
        "scripts/aster-adaptive/sa4_root_transaction_owner_v3.py",
        "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v3.py",
        "2b2d08249072c52dd5e2f79ff3f525bdb46c647a79225993e964dd6e7dd49fb0"),
    Change(
        "scripts/aster-adaptive/sa4_fixed_transaction_runner_v3.py",
        "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v3.py",
        "9c6bfbbe05dfa6d574988df3a99b79696fcfee1353d24461324806df2ec0cc9f"),
)
INSTALLED_DEPENDENCIES = {
    "/usr/local/libexec/aster-sa4/sa4_authenticated_authority_v1.py":
        "367bf1a1e473363b8c8aac7d13a4f06456964de45093c172e32a1f3c93a725d6",
    "/usr/local/libexec/aster-sa4/sa4_observer_file_exchange_v1.py":
        "6cddfd315ca70753e7065de7d01eb176f9fc4b0a0d4740d326f3d08be1883a63",
    "/usr/local/libexec/aster-sa4/sa4_one_shot_transaction_controller_v2.py":
        "10d98960957d8226830720cd8c280de0d4b67108a5ae96dc41cce78f7a83daf3",
    "/usr/local/libexec/aster-sa4/sa4_one_use_grant_ledger_v1.py":
        "4babcb5bd08d13788c4f0fb52447ad35e892fb2264b7b7bcadddabfd88e738b0",
    "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v2.py":
        "a97645ae5365c1121d6acc9ed778bb769f442bb964b21a2687d46443ba7269bc",
    "/usr/local/libexec/aster-sa4/sa4_single_file_repair_contract_v1.py":
        "c260e6d8f5ce0546bf4a2f3754bda02a55731bbb69a6c869917840cf3ebb9467",
    "/usr/local/libexec/aster-sa4/sa4_target_registry_v2.py":
        "86c442725544480c85c6bdb5507c17d48acc16e58994e32fffaae944f696da39",
}
TARGET_PATH = "/var/lib/aster/sa4/canary-adapter-v2.json"
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")


def validate() -> None:
    if len(CHANGES) != 2 or len({item.destination for item in CHANGES}) != 2:
        raise ValueError("SA4 distinct-canary v3 install set changed")
    for item in CHANGES:
        if (hashlib.sha256((ROOT / item.source).read_bytes()).hexdigest()
                != item.after_sha256):
            raise ValueError("SA4 distinct-canary v3 source changed")
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith(
                    "/usr/local/libexec/aster-sa4/")
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")):
            raise ValueError("unsafe SA4 distinct-canary v3 install")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-distinct-canary-v3-inactive-install-plan.v1",
        "host": "lxc104",
        "changes": [asdict(item) for item in CHANGES],
        "installed_dependencies": dict(INSTALLED_DEPENDENCIES),
        "target": {"path": TARGET_PATH, "sha256": TARGET_SHA256},
        "precondition": [
            "both-destinations-absent", "exact-installed-dependencies",
            "exact-drifted-v2-canary", "lease-ready",
            "operation-lock-and-emergency-stop-absent",
            "v2-input-evidence-ledger-absent", "production-healthy",
        ],
        "postcheck": [
            "exact-root-owned-single-link-files", "isolated-imports-only",
            "spent-v1-target-rejected", "v2-target-resolves",
            "no-v3-runner-invocation", "no-transaction-state",
            "target-unchanged", "production-healthy",
        ],
        "rollback": {
            "remove-only-exact-after-hashes": [
                item.destination for item in reversed(CHANGES)],
            "uncertainty": "retain-and-stop",
        },
        "effect_authorized": False,
        "automatic_routing": "off",
        "exclusions": [
            "no-signer", "no-authority", "no-ledger-claim",
            "no-checkpoint", "no-repair", "no-service-action",
            "no-route-or-promotion",
        ],
    }


validate()

