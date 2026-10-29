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
                             expected_uid: int = 0) -> dict[str, object]:
    """Validate a root-owned, inert SA3 installation without executing it.

    The dependency-closure check is intentional.  A workload cannot become
    admitted merely because its named files hash correctly while one of
    their local imports is omitted from the registration.
    """
    spec = workload("sa3-expanded-source-quality-v1")
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
    missing = sorted(name for name in imports if name in {
        "sa3_expanded_quality_packet", "sa3_expanded_quality_runner", "sa3_fair_scorer"
    } and name not in local_modules)
    if missing:
        raise ValueError("unregistered local dependency:" + ",".join(missing))

    unit_root = Path("/etc/systemd/system") if unit_root is None else Path(unit_root)
    target_prefix = unit_root / "aster-lab-hours-booking-sa3-expanded-source-quality-v1"
    for suffix in (".service", ".timer"):
        if (target_prefix.with_suffix(suffix)).exists():
            raise ValueError(f"target unit must remain inactive:{suffix}")
    return {"workload_id": spec.workload_id, "runtime_files": len(spec.runtime_pins),
            "target_units": "absent", "effects": "not-attempted"}


validate_registry()
