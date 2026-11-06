"""Exact reversible inactive upgrade plan for the SA4 root owner source."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


LIBEXEC = "/usr/local/libexec/aster-sa4"
CHECKPOINT = "/var/lib/aster/sa4/source-checkpoints/root-owner-rc1"


@dataclass(frozen=True)
class Change:
    source: str
    destination: str
    before_sha256: str | None
    after_sha256: str
    operation: str
    owner: str = "root"
    group: str = "root"
    mode: str = "0644"


CHANGES = (
    Change("scripts/aster-adaptive/sa4_preflight_composition_v1.py",
           f"{LIBEXEC}/sa4_preflight_composition_v1.py",
           "d96fcba0bda17ae48f2061a9c7977bbc70c67271a16d02ed11530b05d0a2ea06",
           "a38ccb0b33bbc828f7ae96fd68304776cd840ea49bb07986044383e42fb1ad11",
           "checkpoint-and-atomic-replace"),
    Change("scripts/aster-adaptive/sa4_receipt_ledger_reconciler_v1.py",
           f"{LIBEXEC}/sa4_receipt_ledger_reconciler_v1.py",
           "d69ef159146aca6ce3830a400c41b17ce794b3c0b7c259b86869c3c3bc29aefc",
           "9688ae6e6d50062a5b31e70bdec87d763d5b378ea681a35c07329f772cd669a1",
           "checkpoint-and-atomic-replace"),
    Change("scripts/aster-adaptive/sa4_effect_admission_v1.py",
           f"{LIBEXEC}/sa4_effect_admission_v1.py", None,
           "16d6bba03357c90da29591513d3e39019400c36dbfe1a6d64f9aef85226c040b",
           "create-exclusive"),
    Change("scripts/aster-adaptive/sa4_root_transaction_owner_v1.py",
           f"{LIBEXEC}/sa4_root_transaction_owner_v1.py", None,
           "d8a6d69a7780e37d483cdc857859314f1613d8ddad56de3c78e46623ea041c39",
           "create-exclusive"),
)


def validate() -> None:
    if (len(CHANGES) != 4 or len({item.destination for item in CHANGES}) != 4
            or sum(item.before_sha256 is not None for item in CHANGES) != 2):
        raise ValueError("SA4 root-owner upgrade set changed")
    for item in CHANGES:
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith(LIBEXEC + "/")
                or item.owner != "root" or item.group != "root"
                or item.mode != "0644"
                or item.operation not in {
                    "checkpoint-and-atomic-replace", "create-exclusive"}
                or (item.before_sha256 is None)
                != (item.operation == "create-exclusive")):
            raise ValueError("unsafe SA4 root-owner upgrade change")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-root-owner-inactive-upgrade-plan.v1",
        "host_id": "lxc104", "changes": [asdict(item) for item in CHANGES],
        "checkpoint": {"path": CHECKPOINT, "owner": "root",
                       "group": "root", "mode": "0700",
                       "retained_file_mode": "0600"},
        "precondition": "exact-before-hash-owner-group-mode-link-count-no-follow",
        "postcondition": "exact-after-hash-owner-group-mode-link-count-no-follow",
        "rollback": {
            "restore_replacements": [item.destination for item in CHANGES
                                      if item.before_sha256 is not None],
            "remove_creations": [item.destination for item in reversed(CHANGES)
                                 if item.before_sha256 is None],
            "precondition": "all-after-hashes-unchanged-no-follow",
            "uncertainty": "retain-and-stop"},
        "effect_authorized": False, "automatic_routing": "off",
        "exclusions": [
            "no-private-key-read-signature-or-credential-action",
            "no-authority-grant-ledger-claim-checkpoint-or-receipt",
            "no-target-write-repair-rollback-or-root-owner-invocation",
            "no-service-restart-reload-unit-timer-booking-or-model-call"]}


validate()
