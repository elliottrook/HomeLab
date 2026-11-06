"""Reversible zero-effect install plan for the joined SA4 transaction source."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


LXC_LIBEXEC = "/usr/local/libexec/aster-sa4"
LXC_CHECKPOINT = "/var/lib/aster/sa4/source-checkpoints/transaction-rc1"
PROXMOX_LIBEXEC = "/usr/local/libexec/aster-sa4"


@dataclass(frozen=True)
class Change:
    host_id: str
    source: str
    destination: str
    old_sha256: str | None
    new_sha256: str
    operation: str
    owner: str = "root"
    group: str = "root"
    mode: str = "0644"


CHANGES = (
    Change("lxc104", "scripts/aster-adaptive/sa4_atomic_repair_owner_v1.py",
           f"{LXC_LIBEXEC}/sa4_atomic_repair_owner_v1.py", None,
           "66f65620de21a6a8fe2a6d01e5b04c12e539d9e06b337a60ad797574036c4020",
           "create-exclusive"),
    Change("lxc104", "scripts/aster-adaptive/sa4_atomic_rollback_owner_v1.py",
           f"{LXC_LIBEXEC}/sa4_atomic_rollback_owner_v1.py", None,
           "fa8c7cf1fd37c76cc6ffe0309182d1655d56e64e43dc6efbb03c844edb2825a0",
           "create-exclusive"),
    Change("lxc104", "scripts/aster-adaptive/sa4_independent_receipt_producer_v1.py",
           f"{LXC_LIBEXEC}/sa4_independent_receipt_producer_v1.py", None,
           "6db243dc23ecbc2786b12a020619def376856a48e730f247bd7f53c56fe79167",
           "create-exclusive"),
    Change("lxc104", "scripts/aster-adaptive/sa4_independent_rollback_receipt_producer_v1.py",
           f"{LXC_LIBEXEC}/sa4_independent_rollback_receipt_producer_v1.py", None,
           "fd63a538e9793650a5da5eab6d205a96908e6d0cd3c41ea942f6c0dfcaef4320",
           "create-exclusive"),
    Change("lxc104", "scripts/aster-adaptive/sa4_independent_postcheck_receipt_v1.py",
           f"{LXC_LIBEXEC}/sa4_independent_postcheck_receipt_v1.py",
           "ab58b635d823a1c82f30d8d89f68c1ed25519914270c7e3d467228bf2452c355",
           "b0a4a3cfe6ad2c53c14c8165fe0a342f6c7eec28d0c5b727579dcbdc0ef6f831",
           "checkpoint-and-atomic-replace"),
    Change("lxc104", "scripts/aster-adaptive/sa4_receipt_ledger_reconciler_v1.py",
           f"{LXC_LIBEXEC}/sa4_receipt_ledger_reconciler_v1.py",
           "873fa76409bdf819bf9bfc32fa13aec4996929eed658c07d595baf1e464bd820",
           "d69ef159146aca6ce3830a400c41b17ce794b3c0b7c259b86869c3c3bc29aefc",
           "checkpoint-and-atomic-replace"),
    Change("proxmox", "scripts/aster-adaptive/sa4_observer_signer_v1.py",
           f"{PROXMOX_LIBEXEC}/sa4_observer_signer_v1.py", None,
           "d804154ca98baeac9a7b4a449be7fe475979e7f3f8be20bb3280b68b0002cf16",
           "create-parent-and-file-exclusive"),
)


def validate() -> None:
    if (len(CHANGES) != 7 or len({item.destination for item in CHANGES}) != 7
            or tuple(item.host_id for item in CHANGES).count("proxmox") != 1
            or tuple(item.host_id for item in CHANGES).count("lxc104") != 6):
        raise ValueError("SA4 transaction install set changed")
    for item in CHANGES:
        if (not item.destination.startswith("/")
                or str(PurePosixPath(item.destination)) != item.destination
                or item.mode != "0644" or item.owner != "root"
                or item.group != "root"
                or item.operation not in {
                    "create-exclusive", "checkpoint-and-atomic-replace",
                    "create-parent-and-file-exclusive"}):
            raise ValueError("unsafe SA4 transaction installation")
    if (sum(item.old_sha256 is not None for item in CHANGES) != 2
            or any((item.old_sha256 is None)
                   != (item.operation != "checkpoint-and-atomic-replace")
                   for item in CHANGES)):
        raise ValueError("SA4 transaction predecessor boundary changed")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-transaction-inactive-install-plan.v1",
        "changes": [asdict(item) for item in CHANGES],
        "lxc_checkpoint": {
            "path": LXC_CHECKPOINT, "owner": "root", "group": "root",
            "mode": "0700", "retained_old_file_mode": "0600"},
        "proxmox_parent": {
            "path": PROXMOX_LIBEXEC, "current_state": "absent",
            "create_owner": "root", "create_group": "root",
            "create_mode": "0755"},
        "postchecks": [
            "all-seven-destination-hashes-and-metadata-exact",
            "all-seven-isolated-imports-pass",
            "three-transaction-host-bindings-remain-unconfigured",
            "observer-signer-self-test-uses-fake-runner-only",
            "joined-disposable-success-and-rollback-rehearsal-passes",
            "no-private-key-signature-grant-checkpoint-repair-or-rollback",
            "production-health-and-schedules-unchanged"],
        "rollback": {
            "lxc": "restore-two-retained-predecessors-and-remove-four-new-files-if-hashes-unchanged",
            "proxmox": "remove-new-signer-and-new-parent-only-if-hash-and-emptiness-unchanged",
            "uncertainty": "retain-and-stop"},
        "effect_authorized": False, "automatic_routing": "off",
        "exclusions": [
            "no-private-key-read-print-copy-export-or-signing",
            "no-live-measurement-or-checkpoint-owner-invocation",
            "no-ledger-initialize-claim-or-finish",
            "no-target-write-repair-rollback-or-receipt",
            "no-service-restart-reload-unit-timer-booking-or-model-call"]}


validate()
