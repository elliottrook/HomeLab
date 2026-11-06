"""Inactive two-file upgrade for corrected SA4 runtime-control ownership."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


LIBEXEC = "/usr/local/libexec/aster-sa4"
CHECKPOINT = "/var/lib/aster/sa4/source-checkpoints/runtime-control-rc1"


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
    Change("scripts/aster-adaptive/sa4_root_transaction_owner_v1.py",
           f"{LIBEXEC}/sa4_root_transaction_owner_v1.py",
           "d8a6d69a7780e37d483cdc857859314f1613d8ddad56de3c78e46623ea041c39",
           "e250bb2cf8bddf86634c973e968a787196ff0ae3fa7eaac10b2cd2d488404e3e",
           "checkpoint-and-atomic-replace"),
    Change("scripts/aster-adaptive/sa4_runtime_control_owner_v1.py",
           f"{LIBEXEC}/sa4_runtime_control_owner_v1.py", None,
           "6d6e89d22829395373089c50eece2ffcdcc042c70c85a25a2f38867f2b330daa",
           "create-exclusive"),
)


def validate() -> None:
    if len(CHANGES) != 2 or len({item.destination for item in CHANGES}) != 2:
        raise ValueError("SA4 runtime-control upgrade set changed")
    for item in CHANGES:
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith(LIBEXEC + "/")
                or item.owner != "root" or item.group != "root"
                or item.mode != "0644"
                or (item.before_sha256 is None)
                != (item.operation == "create-exclusive")):
            raise ValueError("unsafe SA4 runtime-control upgrade")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-runtime-control-inactive-upgrade-plan.v1",
        "host_id": "lxc104", "changes": [asdict(item) for item in CHANGES],
        "checkpoint": {"path": CHECKPOINT, "owner": "root",
                       "group": "root", "mode": "0700",
                       "retained_file_mode": "0600"},
        "precondition": ["lease-ready", "operation-lock-absent",
                         "emergency-stop-absent", "exact-predecessor",
                         "new-path-absent"],
        "rollback": {"restore": CHANGES[0].destination,
                     "remove": CHANGES[1].destination,
                     "only-if-after-hashes-unchanged": True,
                     "uncertainty": "retain-and-stop"},
        "effect_authorized": False, "automatic_routing": "off",
        "exclusions": ["no-key-or-signature", "no-authority-or-grant",
                       "no-lock-or-stop-creation", "no-root-owner-invocation",
                       "no-checkpoint-or-repair", "no-service-action",
                       "no-model-route-schedule-or-booking"]}


validate()
