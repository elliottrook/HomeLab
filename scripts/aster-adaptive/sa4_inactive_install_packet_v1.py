"""Source-only SA4 inactive-install and exact rollback packet.

This module describes an install; it cannot perform one.  The packet is
deliberately inert: it contains no command runner, remote transport, service
unit, timer, booking, key material, grant, repair invocation or restart.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
import re


HEX64 = re.compile(r"[0-9a-f]{64}")
LIBEXEC = "/usr/local/libexec/aster-sa4"
STATE = "/var/lib/aster/sa4"
TARGET = f"{STATE}/canary-adapter.json"
CHECKPOINTS = f"{STATE}/checkpoints"


@dataclass(frozen=True)
class Payload:
    source: str
    destination: str
    sha256: str
    owner: str = "root"
    group: str = "root"
    mode: str = "0644"


DIRECTORIES = (
    (LIBEXEC, "root", "root", "0755"),
    (STATE, "root", "root", "0700"),
    (CHECKPOINTS, "root", "root", "0700"),
)

_PROGRAMS = (
    ("nlu_threshold_policy.py", "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d"),
    ("sa4_authenticated_authority_v1.py", "cbc976176841890ba53e2458e55f09c33c802605cfa43ea8c2c3bdd8766be6ee"),
    ("sa4_canary_consumer_health_check_v1.py", "1214189f36c4bb75a90028cd31c15f4dd5ecf6977582ada67cd72a5ce65c72da"),
    ("sa4_canary_rollback_check_v1.py", "15f924f589980d786e7d0f8ad5ac5f03e32e95d907737a6c2d4ae9adad61ffdb"),
    ("sa4_canary_target_bytes_check_v1.py", "f8f544ca04b7587b76d827ea1e193c56bb814a231b498c6652009e098bdd00a1"),
    ("sa4_canary_target_metadata_check_v1.py", "e61bb89bd366e03fed0bafaa23b18db484f1b2a6133b2a708469b9b66d49a041"),
    ("sa4_filesystem_evidence_v1.py", "6ea2b5da108b46be8ff0682f4d3dd2c66316530cb9f09316347f2cfd85f7cbc0"),
    ("sa4_inactive_checkpoint_owner_v1.py", "fe8f6385b8fe506b3d81cbc5cdce133be9761b17957871430f7904484db4c45f"),
    ("sa4_inactive_measurement_owner_v1.py", "aa6ebfb2cb24f7ba2fc3ef994cbe463d0019587ee4bd0662ffdd8512827ec70f"),
    ("sa4_independent_postcheck_receipt_v1.py", "a1e99c3abbe90ed788a33118b40d3630d34b740a09e72067871515cf3e145b9d"),
    ("sa4_key_custody_slots_v1.py", "6e45ecad5bf7d1f7b80e040b9b24b380ef21a9f3343e93f127f0ffb246e04816"),
    ("sa4_one_use_grant_ledger_v1.py", "4babcb5bd08d13788c4f0fb52447ad35e892fb2264b7b7bcadddabfd88e738b0"),
    ("sa4_preflight_composition_v1.py", "a45335dcb6ab209433e71bd486345904d4e0748f5ae03bc85f24a7863926b569"),
    ("sa4_receipt_ledger_reconciler_v1.py", "873fa76409bdf819bf9bfc32fa13aec4996929eed658c07d595baf1e464bd820"),
    ("sa4_single_file_repair_contract_v1.py", "c260e6d8f5ce0546bf4a2f3754bda02a55731bbb69a6c869917840cf3ebb9467"),
    ("sa4_single_file_repair_receipt_v1.py", "14ce759948a7a39f9da4ee7651f97a2a4ed42885e61047bbf84def76172a42c1"),
    ("sa4_target_registry_v1.py", "0091a90f60eb57e4776bd1e73e85286d7a00bf026b21255361d618e2713b9d83"),
)

PAYLOADS = tuple(
    Payload(f"scripts/aster-adaptive/{name}", f"{LIBEXEC}/{name}", digest)
    for name, digest in _PROGRAMS
) + (
    Payload(
        "scripts/aster-adaptive/fixtures/sa4-canary-adapter-drifted-v1.json",
        TARGET,
        "19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a",
    ),
)

EXCLUSIONS = (
    "no-private-or-public-key-creation",
    "no-grant-or-authority",
    "no-checkpoint-or-repair-effect",
    "no-service-unit-timer-or-booking",
    "no-restart-reload-routing-or-model-change",
    "no-overwrite-of-existing-path",
)


def _absolute_clean(path: str) -> bool:
    return (path.startswith("/") and path == str(PurePosixPath(path))
            and ".." not in PurePosixPath(path).parts and "\x00" not in path)


def validate_packet() -> None:
    if DIRECTORIES != (
        (LIBEXEC, "root", "root", "0755"),
        (STATE, "root", "root", "0700"),
        (CHECKPOINTS, "root", "root", "0700"),
    ):
        raise ValueError("SA4 directory set changed")
    if len(PAYLOADS) != 18 or len({p.destination for p in PAYLOADS}) != 18:
        raise ValueError("SA4 payload set must contain 18 unique paths")
    for payload in PAYLOADS:
        if (not _absolute_clean(payload.destination)
                or not HEX64.fullmatch(payload.sha256)
                or payload.owner != "root" or payload.group != "root"
                or payload.mode != "0644"
                or not (payload.destination.startswith(LIBEXEC + "/")
                        or payload.destination == TARGET)):
            raise ValueError("unsafe SA4 inactive-install payload")


def plan(*, observed_absent_paths: set[str]) -> dict[str, object]:
    """Return an exact no-overwrite plan after an all-paths-absent preflight."""
    validate_packet()
    required_absent = {path for path, _, _, _ in DIRECTORIES}
    required_absent.update(payload.destination for payload in PAYLOADS)
    if observed_absent_paths != required_absent:
        raise ValueError("exact SA4 absence proof required")
    return {
        "schema": "aster-sa4-inactive-install-plan.v1",
        "host_id": "lxc104",
        "directories": [list(item) for item in DIRECTORIES],
        "payloads": [payload.__dict__ for payload in PAYLOADS],
        "precondition": "all-listed-paths-absent-no-follow",
        "postcondition": "exact-hash-owner-group-mode-no-follow",
        "rollback": {
            "remove_files": [p.destination for p in reversed(PAYLOADS)],
            "remove_empty_directories": [CHECKPOINTS, STATE, LIBEXEC],
            "precondition": "installed-by-this-packet-and-exact-hashes-unchanged",
            "on_uncertainty": "retain-and-stop",
        },
        "effect_authorized": False,
        "automatic_routing": "off",
        "key_slots_populated": False,
        "exclusions": list(EXCLUSIONS),
    }


validate_packet()
