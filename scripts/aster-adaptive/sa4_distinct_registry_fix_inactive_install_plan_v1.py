"""Inactive install plan for the complete distinct-registry correction."""
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
        "scripts/aster-adaptive/sa4_distinct_registry_bindings_v1.py",
        "/usr/local/libexec/aster-sa4/sa4_distinct_registry_bindings_v1.py",
        "c88640a32fb9a413afcd01e2dcdadcb4a5fc68f0bdd99a59e976aa5f83476330"),
    Change(
        "scripts/aster-adaptive/sa4_root_transaction_owner_v4.py",
        "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v4.py",
        "9da52be5fba3d9a5c628e94a887f034944d6a75f31bf8dbb86471005ff5453e6"),
    Change(
        "scripts/aster-adaptive/sa4_fixed_transaction_runner_v4.py",
        "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v4.py",
        "ab2c67cd1640cbb60b3da89aadc9f90ee34132873295f8736f10ed0af3b79d0f"),
)

INSTALLED_DEPENDENCIES = {
    "/usr/local/libexec/aster-sa4/sa4_atomic_repair_owner_v1.py":
        "66f65620de21a6a8fe2a6d01e5b04c12e539d9e06b337a60ad797574036c4020",
    "/usr/local/libexec/aster-sa4/sa4_atomic_rollback_owner_v1.py":
        "fa8c7cf1fd37c76cc6ffe0309182d1655d56e64e43dc6efbb03c844edb2825a0",
    "/usr/local/libexec/aster-sa4/sa4_effect_admission_v1.py":
        "16d6bba03357c90da29591513d3e39019400c36dbfe1a6d64f9aef85226c040b",
    "/usr/local/libexec/aster-sa4/sa4_inactive_checkpoint_owner_v1.py":
        "b0d8dff3bf7714cfc48e1dc5ea6e5e40db8ff815410c631e036880d79b307614",
    "/usr/local/libexec/aster-sa4/sa4_inactive_measurement_owner_v1.py":
        "16644ee6dd42997bd07993ce0a850fc6620208e27b3c81ba03069f8ea91e5e2e",
    "/usr/local/libexec/aster-sa4/sa4_independent_postcheck_receipt_v1.py":
        "b0a4a3cfe6ad2c53c14c8165fe0a342f6c7eec28d0c5b727579dcbdc0ef6f831",
    "/usr/local/libexec/aster-sa4/sa4_independent_receipt_producer_v1.py":
        "6db243dc23ecbc2786b12a020619def376856a48e730f247bd7f53c56fe79167",
    "/usr/local/libexec/aster-sa4/sa4_independent_rollback_receipt_producer_v1.py":
        "fd63a538e9793650a5da5eab6d205a96908e6d0cd3c41ea942f6c0dfcaef4320",
    "/usr/local/libexec/aster-sa4/sa4_preflight_composition_v1.py":
        "a38ccb0b33bbc828f7ae96fd68304776cd840ea49bb07986044383e42fb1ad11",
    "/usr/local/libexec/aster-sa4/sa4_receipt_ledger_reconciler_v2.py":
        "9889f6436c645be9fa735cb7428cc95e717ead87dc82b2f0a2b1b08c06abf41e",
    "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v2.py":
        "a97645ae5365c1121d6acc9ed778bb769f442bb964b21a2687d46443ba7269bc",
    "/usr/local/libexec/aster-sa4/sa4_runtime_control_owner_v1.py":
        "6d6e89d22829395373089c50eece2ffcdcc042c70c85a25a2f38867f2b330daa",
    "/usr/local/libexec/aster-sa4/sa4_single_file_repair_contract_v1.py":
        "c260e6d8f5ce0546bf4a2f3754bda02a55731bbb69a6c869917840cf3ebb9467",
    "/usr/local/libexec/aster-sa4/sa4_target_registry_v1.py":
        "0091a90f60eb57e4776bd1e73e85286d7a00bf026b21255361d618e2713b9d83",
    "/usr/local/libexec/aster-sa4/sa4_target_registry_v2.py":
        "86c442725544480c85c6bdb5507c17d48acc16e58994e32fffaae944f696da39",
    "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v3.py":
        "9c6bfbbe05dfa6d574988df3a99b79696fcfee1353d24461324806df2ec0cc9f",
}
INSTALL_RESULT_SHA256 = (
    "7143c186f8dbefb7f39bd958d6cda8a0f263d0fb2efd5de7a2dba57fa7cff9fc")
TARGET_PATH = "/var/lib/aster/sa4/canary-adapter-v2.json"
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")


def validate() -> None:
    if len(CHANGES) != 3 or len({item.destination for item in CHANGES}) != 3:
        raise ValueError("SA4 distinct registry correction set changed")
    for item in CHANGES:
        if hashlib.sha256((ROOT / item.source).read_bytes()).hexdigest() != item.after_sha256:
            raise ValueError("SA4 distinct registry correction source changed")
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith("/usr/local/libexec/aster-sa4/")
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")):
            raise ValueError("unsafe SA4 distinct registry correction install")
    result = ROOT / (
        "docs/projects/AI Projects/evidence/"
        "SA4-distinct-canary-v3-inactive-install-result-2026-11-06.json")
    if hashlib.sha256(result.read_bytes()).hexdigest() != INSTALL_RESULT_SHA256:
        raise ValueError("SA4 distinct registry predecessor result changed")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-distinct-registry-fix-inactive-install-plan.v1",
        "host": "lxc104",
        "changes": [asdict(item) for item in CHANGES],
        "installed_dependencies": dict(INSTALLED_DEPENDENCIES),
        "predecessor_install_result_sha256": INSTALL_RESULT_SHA256,
        "target": {"path": TARGET_PATH, "sha256": TARGET_SHA256},
        "precondition": [
            "all-three-destinations-absent", "exact-installed-dependencies",
            "exact-predecessor-result", "exact-drifted-v2-canary",
            "lease-ready", "operation-lock-and-emergency-stop-absent",
            "v2-input-evidence-ledger-absent", "production-healthy",
        ],
        "postcheck": [
            "exact-root-owned-single-link-files", "isolated-imports-only",
            "v1-plan-rejects-distinct-target",
            "complete-v2-binding-accepts-and-restores-v1",
            "final-v4-runner-rejects-arguments-before-input",
            "no-transaction-state", "target-unchanged", "production-healthy",
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

