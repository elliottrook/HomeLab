"""Fixed, root-installed Lab Hours workload registrations.

This module is deliberately data-only at the admission boundary: booking
records select a registered identity, never an arbitrary command.  The
platform runner validates the selected identity and its pinned runtime files
before any effect.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path


@dataclass(frozen=True)
class WorkloadSpec:
    workload_id: str
    owner: str
    request_count: int
    per_request_timeout_seconds: int
    deadline_seconds: int
    minimum_booking_seconds: int
    recovery_reserve_seconds: int
    runner_kind: str
    runtime_pins: tuple[tuple[str, str], ...]
    packet_sha256: str | None = None
    result_max_bytes: int | None = None

    @property
    def rescue_after_seconds(self) -> int:
        return self.deadline_seconds


ACCEPTED_BASELINE_PINS = (
    ("model_sha256", "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"),
    ("binary_sha256", "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"),
    ("unit_sha256", "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"),
)


WORKLOADS = {
    "accepted-9b-direct-control-smoke-v1": WorkloadSpec(
        workload_id="accepted-9b-direct-control-smoke-v1", owner="lab-hours",
        request_count=3, per_request_timeout_seconds=120, deadline_seconds=1800,
        minimum_booking_seconds=1800, recovery_reserve_seconds=900,
        runner_kind="full-inference-pilot", runtime_pins=(),
    ),
    "accepted-9b-owner-loss-exercise-v1": WorkloadSpec(
        workload_id="accepted-9b-owner-loss-exercise-v1", owner="lab-hours",
        request_count=0, per_request_timeout_seconds=0, deadline_seconds=120,
        minimum_booking_seconds=300, recovery_reserve_seconds=120,
        runner_kind="owner-loss-exercise", runtime_pins=(),
    ),
    "sa3-expanded-source-quality-v1": WorkloadSpec(
        workload_id="sa3-expanded-source-quality-v1", owner="aster-stream-a",
        request_count=20, per_request_timeout_seconds=120, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="sa3-expanded-quality", runtime_pins=(
            ("sa3-expanded-source-quality-v1.json",
             "ed75836af74401709a74333a96d0a22629b23e389e5262bbc365ab6aed018d23"),
            ("sa3_expanded_quality_packet.py",
             "b9011bef592421b6e6c28ec830b17f1296409daa30fd4f508d913ba35c104657"),
            ("sa3_expanded_quality_runner.py",
             "39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351"),
            ("sa3_fair_scorer.py",
             "92a4526886b21492995b73c834844a570b7718415abcadce848bcd1da6860bda"),
        ),
        packet_sha256="d8c7945924a98bfae45522fd4ac9f377871db3243136b4a00617263cf44e9066",
        result_max_bytes=262144,
    ),
    "m3-joint-semantic-35b-public-v1": WorkloadSpec(
        workload_id="m3-joint-semantic-35b-public-v1", owner="aster-stream-a",
        request_count=24, per_request_timeout_seconds=90, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="m3-joint-semantic-35b", runtime_pins=(
            ("nlu_joint_semantic_35b_v1.py", "b2682aa294e5d29b36c961c0b6b5b1593312781026c4f1e3424836ee44f63309"),
            ("nlu_joint_semantic_35b_public_runner_v1.py", "b91e2dc3c2b6c8fbb89d912d8789ea2ac49d6ac412d9e77f854f66c259ac18d3"),
            ("nlu_whole_label_public_runner_v1.py", "fe5186020f9fcad1bbe25f72f3a22c95a1d9ed23342aef611dd510d59a1b45f3"),
            ("nlu_whole_label_choice_v1.py", "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a"),
            ("nlu_deterministic_guard_v1.py", "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135"),
            ("nlu_local_model_adapter.py", "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0"),
            ("nlu_threshold_policy.py", "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d"),
            ("nlu-development-v1.json", "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"),
            ("m3_joint_semantic_35b_guest_workload.py", "91fa17ad55177b5d2c53fefb8569c13c48e1bfeec8332b97726e8d30bab0d85b"),
            ("m3_joint_semantic_35b_transaction.py", "dc92e35ee11ed12cd5d842282027adbcbf4c24611ba6b4be64a820fa951f0677"),
            ("m3_joint_semantic_35b_guardian.py", "a485c2cde71447a8a4feda0c25f7e22d26fe0e9ace2da7b524e698a96275113b"),
            ("full_aster_first_screen_candidate.py", "eb07b46c1f592ef35c9e0bcb7f0f6aaa0d484775e18ab991b6c29dbe1dc2af6b"),
            ("full_aster_first_screen_observer.py", "277fa96f411737e265f3fcfb3169d00a3dfb0289d5b075150f677b04469ce340"),
            ("full_aster_first_screen_recovery.py", "992e7d4bbf8b0f62cc72546dae9ad2ab9622830deef78d096afc028c2b5eb3f4"),
        ),
        packet_sha256="1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785",
        result_max_bytes=262144,
    ),
    "sa3-evidence-envelope-quality-v1": WorkloadSpec(
        workload_id="sa3-evidence-envelope-quality-v1", owner="aster-stream-a",
        request_count=20, per_request_timeout_seconds=120, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="sa3-evidence-envelope-quality", runtime_pins=(
            ("sa3-evidence-envelope-quality-v1.json",
             "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a"),
            ("sa3_deterministic_evidence_envelope_v1.py",
             "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3"),
            ("sa3_evidence_envelope_batch_v1.py",
             "78abc29951fe80a469c49ee44af6a9380f032648ad757f3182c11bd0f0464500"),
            ("sa3_evidence_envelope_quality_freeze_v1.py",
             "95cf006fc7e3b2aeb3acf0e926336e65e3c3a8b5e5f8cb5cc083e4e5ab7b3483"),
            ("sa3_evidence_envelope_runner_v1.py",
             "372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352"),
        ),
        packet_sha256="a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a",
        result_max_bytes=524288,
    ),
    "sa3-evidence-envelope-candidate-i-quality-v1": WorkloadSpec(
        workload_id="sa3-evidence-envelope-candidate-i-quality-v1",
        owner="aster-stream-a",
        request_count=20, per_request_timeout_seconds=120, deadline_seconds=2700,
        minimum_booking_seconds=3600, recovery_reserve_seconds=900,
        runner_kind="sa3-evidence-envelope-candidate-i-quality", runtime_pins=(
            ("sa3-evidence-envelope-candidate-i-quality-v1.json",
             "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0"),
            ("sa3_deterministic_evidence_envelope_v1.py",
             "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3"),
            ("sa3_deterministic_evidence_envelope_v2.py",
             "4ca154c6ea0b0738adc3c9e21544ac0a6d3c05473852f88f97b6e5e7e1611943"),
            ("sa3_evidence_envelope_batch_v2.py",
             "eaeddb10d5a36df5dd3f3646691d19857f094f2872086d7b78056d6ff7c70d4e"),
            ("sa3_evidence_envelope_runner_v2.py",
             "58b932a65afb6d88d4624d3d74b0d4d021091e0989c74e1ca4cf0afdede9188c"),
        ),
        packet_sha256="0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0",
        result_max_bytes=524288,
    ),
}


REGISTERED_WORKLOADS = frozenset(WORKLOADS)


def workload(name: str) -> WorkloadSpec:
    try:
        return WORKLOADS[name]
    except KeyError as exc:
        raise ValueError("workload is not registered") from exc


def validate_registry() -> None:
    sa3 = workload("sa3-expanded-source-quality-v1")
    if sa3.request_count != 20 or sa3.deadline_seconds != 2700:
        raise ValueError("SA3 workload budget drift")
    if sa3.minimum_booking_seconds != 3600 or sa3.recovery_reserve_seconds != 900:
        raise ValueError("SA3 booking boundary drift")
    if sa3.runner_kind != "sa3-expanded-quality" or len(sa3.runtime_pins) != 4:
        raise ValueError("SA3 runner registration drift")
    if sa3.result_max_bytes != 262144 or not sa3.packet_sha256:
        raise ValueError("SA3 result boundary drift")
    if any(name.endswith("keys-v1.json") or "review" in name
           for name, _ in sa3.runtime_pins):
        raise ValueError("SA3 excluded material entered runtime registration")
    m3 = workload("m3-joint-semantic-35b-public-v1")
    if (m3.request_count != 24 or m3.deadline_seconds != 2700
            or m3.minimum_booking_seconds != 3600
            or m3.recovery_reserve_seconds != 900
            or m3.runner_kind != "m3-joint-semantic-35b"
            or len(m3.runtime_pins) != 14
            or m3.packet_sha256 != "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"):
        raise ValueError("M3 workload registration drift")
    envelope = workload("sa3-evidence-envelope-quality-v1")
    if (envelope.owner != "aster-stream-a"
            or envelope.request_count != 20
            or envelope.per_request_timeout_seconds != 120
            or envelope.deadline_seconds != 2700
            or envelope.minimum_booking_seconds != 3600
            or envelope.recovery_reserve_seconds != 900
            or envelope.runner_kind != "sa3-evidence-envelope-quality"
            or len(envelope.runtime_pins) != 5
            or envelope.packet_sha256 != "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a"
            or envelope.result_max_bytes != 524288):
        raise ValueError("SA3 evidence-envelope registration drift")
    if any("keys" in name or "review" in name for name, _ in envelope.runtime_pins):
        raise ValueError("SA3 evidence-envelope excluded material entered runtime registration")
    candidate_i = workload("sa3-evidence-envelope-candidate-i-quality-v1")
    if (candidate_i.owner != "aster-stream-a"
            or candidate_i.request_count != 20
            or candidate_i.per_request_timeout_seconds != 120
            or candidate_i.deadline_seconds != 2700
            or candidate_i.minimum_booking_seconds != 3600
            or candidate_i.recovery_reserve_seconds != 900
            or candidate_i.runner_kind != "sa3-evidence-envelope-candidate-i-quality"
            or len(candidate_i.runtime_pins) != 5
            or candidate_i.packet_sha256 !=
                "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0"
            or candidate_i.result_max_bytes != 524288):
        raise ValueError("SA3 candidate-i registration drift")
    if any("keys" in name or "review" in name
           for name, _ in candidate_i.runtime_pins):
        raise ValueError("SA3 candidate-i excluded material entered runtime registration")


def _local_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".", 1)[0])
    return names


def validate_inactive_target(pilot_root: Path, *, unit_root: Path | None = None,
                             expected_uid: int = 0,
                             workload_id: str = "sa3-expanded-source-quality-v1") -> dict[str, object]:
    """Validate a root-owned, inert SA3 installation without executing it.

    The dependency-closure check is intentional.  A workload cannot become
    admitted merely because its named files hash correctly while one of
    their local imports is omitted from the registration.
    """
    spec = workload(workload_id)
    root = Path(pilot_root)
    for name, expected in spec.runtime_pins:
        path = root / name
        try:
            stat = path.lstat()
        except FileNotFoundError as exc:
            raise ValueError(f"target file missing:{name}") from exc
        if (not path.is_file() or path.is_symlink() or stat.st_uid != expected_uid
                or stat.st_nlink != 1 or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
            raise ValueError(f"target pin or custody mismatch:{name}")

    local_modules = {Path(name).stem for name, _ in spec.runtime_pins if name.endswith(".py")}
    imports = set()
    for name, _ in spec.runtime_pins:
        if name.endswith(".py"):
            imports.update(_local_imports(root / name))
    registered_local_modules = {
        Path(name).stem for item in WORKLOADS.values()
        for name, _ in item.runtime_pins if name.endswith(".py")
    }
    missing = sorted(name for name in imports
                     if name in registered_local_modules and name not in local_modules)
    if missing:
        raise ValueError("unregistered local dependency:" + ",".join(missing))

    unit_root = Path("/etc/systemd/system") if unit_root is None else Path(unit_root)
    target_prefix = unit_root / f"aster-lab-hours-booking-{spec.workload_id}"
    for suffix in (".service", ".timer"):
        if (target_prefix.with_suffix(suffix)).exists():
            raise ValueError(f"target unit must remain inactive:{suffix}")
    return {"workload_id": spec.workload_id, "runtime_files": len(spec.runtime_pins),
            "target_units": "absent", "effects": "not-attempted"}


validate_registry()
