"""Inactive install plan for the fixed SA4 effect controller protocol."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath

@dataclass(frozen=True)
class Change:
    host: str; source: str; destination: str; after_sha256: str
    owner: str = "root"; group: str = "root"; mode: str = "0644"
    operation: str = "create-exclusive"

CHANGES = (
    Change("lxc104", "scripts/aster-adaptive/sa4_one_shot_transaction_controller_v1.py", "/usr/local/libexec/aster-sa4/sa4_one_shot_transaction_controller_v1.py", "4d7a2392c5b424a26e28a13e5205f144b1c27910929c8caaccf2b428188e11e7"),
    Change("lxc104", "scripts/aster-adaptive/sa4_observer_file_exchange_v1.py", "/usr/local/libexec/aster-sa4/sa4_observer_file_exchange_v1.py", "6cddfd315ca70753e7065de7d01eb176f9fc4b0a0d4740d326f3d08be1883a63"),
    Change("proxmox", "scripts/aster-adaptive/sa4_proxmox_observer_bridge_v1.py", "/usr/local/libexec/aster-sa4/sa4_proxmox_observer_bridge_v1.py", "f6f6016c683b700ccda3806de99c500d3f24cab624eee89dd3a44791564d8632"),
)
OBSERVER_SIGNER_SHA256 = "d804154ca98baeac9a7b4a449be7fe475979e7f3f8be20bb3280b68b0002cf16"

def validate() -> None:
    if len(CHANGES) != 3 or len({x.destination for x in CHANGES}) != 3:
        raise ValueError("SA4 effect controller install set changed")
    for item in CHANGES:
        if (str(PurePosixPath(item.destination)) != item.destination
                or not item.destination.startswith("/usr/local/libexec/aster-sa4/")
                or item.host not in {"lxc104", "proxmox"}
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")):
            raise ValueError("unsafe SA4 effect controller install")

def plan() -> dict[str, object]:
    validate()
    return {"schema":"aster-sa4-effect-controller-inactive-install-plan.v1",
            "changes":[asdict(x) for x in CHANGES],
            "precondition":["all-destinations-absent","lease-ready","operation-lock-absent","emergency-stop-absent","exact-observer-signer"],
            "observer_signer_sha256":OBSERVER_SIGNER_SHA256,
            "rollback":{"remove-only-exact-after-hashes":[x.destination for x in reversed(CHANGES)],"uncertainty":"retain-and-stop"},
            "effect_authorized":False,"automatic_routing":"off",
            "exclusions":["no-key-or-signature","no-authority-or-grant","no-runtime-directory","no-controller-invocation","no-target-effect","no-service-action"]}

validate()
