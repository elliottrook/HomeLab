"""Inactive create-only install plan for the accepted distinct SA4 canary."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class Change:
    source: str
    destination: str
    after_sha256: str
    kind: str
    owner: str = "root"
    group: str = "root"
    mode: str = "0644"
    operation: str = "create-exclusive"


CHANGES = (
    Change(
        "scripts/aster-adaptive/sa4_target_registry_v2.py",
        "/usr/local/libexec/aster-sa4/sa4_target_registry_v2.py",
        "86c442725544480c85c6bdb5507c17d48acc16e58994e32fffaae944f696da39",
        "inactive-registry"),
    Change(
        "scripts/aster-adaptive/fixtures/sa4-canary-adapter-v2-drifted.json",
        "/var/lib/aster/sa4/canary-adapter-v2.json",
        "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0",
        "inert-canary-seed"),
)
V1_REGISTRY_SHA256 = \
    "0091a90f60eb57e4776bd1e73e85286d7a00bf026b21255361d618e2713b9d83"
OWNER_ACCEPTANCE_SHA256 = \
    "53070fd50f53ae288d44d3c5e67892090a08387d510a1cd6731cb84102871422"


def validate() -> None:
    if len(CHANGES) != 2 or len({item.destination for item in CHANGES}) != 2:
        raise ValueError("SA4 distinct-canary seed set changed")
    for item in CHANGES:
        if (str(PurePosixPath(item.destination)) != item.destination
                or (item.owner, item.group, item.mode, item.operation)
                != ("root", "root", "0644", "create-exclusive")
                or item.kind not in {"inactive-registry", "inert-canary-seed"}):
            raise ValueError("unsafe SA4 distinct-canary seed install")


def plan() -> dict[str, object]:
    validate()
    return {
        "schema": "aster-sa4-distinct-canary-seed-inactive-install-plan.v1",
        "host": "lxc104",
        "changes": [asdict(item) for item in CHANGES],
        "v1_registry_sha256": V1_REGISTRY_SHA256,
        "owner_acceptance_sha256": OWNER_ACCEPTANCE_SHA256,
        "precondition": [
            "destinations-absent", "exact-v1-registry", "lease-ready",
            "operation-lock-absent", "emergency-stop-absent",
            "existing-canary-healthy", "production-healthy"],
        "postcheck": [
            "exact-root-owned-single-link-files", "isolated-registry-import",
            "v1-target-unchanged", "v2-target-resolves-only-in-v2-registry",
            "no-runner-or-signer", "runtime-state-absent",
            "production-healthy"],
        "rollback": {
            "remove-only-exact-after-hashes": [
                item.destination for item in reversed(CHANGES)],
            "uncertainty": "retain-and-stop"},
        "effect_authorized": False,
        "repair_authorized": False,
        "automatic_routing": "off",
        "exclusions": [
            "no-existing-canary-touch", "no-runner", "no-signer", "no-grant",
            "no-ledger", "no-service-action", "no-route-or-promotion"],
    }


validate()
