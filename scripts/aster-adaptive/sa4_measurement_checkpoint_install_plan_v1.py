"""Inert two-file install plan for LXC104 SA4 measurement ownership."""
from __future__ import annotations

from dataclasses import asdict, dataclass


LIBEXEC = "/usr/local/libexec/aster-sa4"
CHECKPOINT = "/var/lib/aster/sa4/source-checkpoints/measurement-owner-v1"


@dataclass(frozen=True)
class Change:
    source: str
    destination: str
    old_sha256: str
    new_sha256: str


CHANGES = (
    Change(
        "scripts/aster-adaptive/sa4_inactive_measurement_owner_v1.py",
        f"{LIBEXEC}/sa4_inactive_measurement_owner_v1.py",
        "aa6ebfb2cb24f7ba2fc3ef994cbe463d0019587ee4bd0662ffdd8512827ec70f",
        "16644ee6dd42997bd07993ce0a850fc6620208e27b3c81ba03069f8ea91e5e2e",
    ),
    Change(
        "scripts/aster-adaptive/sa4_inactive_checkpoint_owner_v1.py",
        f"{LIBEXEC}/sa4_inactive_checkpoint_owner_v1.py",
        "fe8f6385b8fe506b3d81cbc5cdce133be9761b17957871430f7904484db4c45f",
        "b0d8dff3bf7714cfc48e1dc5ea6e5e40db8ff815410c631e036880d79b307614",
    ),
)


def plan() -> dict[str, object]:
    if len(CHANGES) != 2 or len({item.destination for item in CHANGES}) != 2:
        raise ValueError("SA4 measurement install set changed")
    return {
        "schema": "aster-sa4-measurement-checkpoint-install-plan.v1",
        "host_id": "lxc104",
        "changes": [asdict(item) for item in CHANGES],
        "checkpoint": {"path": CHECKPOINT, "owner": "root", "group": "root",
                       "mode": "0700", "retained_file_mode": "0600"},
        "postchecks": [
            "exact-installed-hash-owner-group-mode",
            "isolated-import-local-host-lxc104",
            "one-read-only-live-measurement",
            "no-checkpoint-claim-receipt-repair-or-service-action",
        ],
        "rollback": "restore-both-retained-files-atomically-on-any-failure",
        "effect_authorized": False,
        "automatic_routing": "off",
        "exclusions": [
            "no-checkpoint-owner-invocation", "no-private-key-or-signing",
            "no-grant-or-ledger-claim", "no-target-write-or-repair",
            "no-service-restart-reload-unit-timer-or-booking",
        ],
    }


plan()

