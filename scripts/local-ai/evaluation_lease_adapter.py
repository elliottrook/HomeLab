"""Effect adapter for the Stream A endpoint-retaining evaluation lease.

The adapter is deliberately disabled unless a future production constructor
supplies ``allow_effects=True``.  Its command surface is allowlisted to the
four registered consumers; the accepted llama service is never a command
target.  Recovery retains durable state and the lock on any uncertainty.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

from evaluation_lease import (
    Admission,
    BACKEND_TARGET,
    EvaluationLeaseError,
    LeaseState,
    ProductionBaseline,
    QUIESCE_TARGETS,
    validate_admission,
    validate_post_quiescence,
    validate_restoration,
    validate_baseline,
)


class AdapterError(EvaluationLeaseError):
    pass


@dataclass(frozen=True)
class AdapterState:
    lease_id: str
    generation: int
    phase: str
    baseline: ProductionBaseline
    window_start_epoch: int
    hard_deadline_epoch: int
    restore_deadline_epoch: int


def source_hashes(root: Path, relative_paths: tuple[str, ...]) -> dict[str, str]:
    """Hash only regular, non-symlink source files beneath the repository root."""
    result: dict[str, str] = {}
    for relative in relative_paths:
        path = root / relative
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise AdapterError(f"source pin is not a regular file: {relative}")
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def consumer_command(target: str, action: str) -> tuple[str, ...]:
    if target not in QUIESCE_TARGETS or action not in {"stop", "mask", "unmask", "start"}:
        raise AdapterError("command target is outside the evaluation allowlist")
    vmid, unit = target.split(":", 1)
    if action == "mask":
        return ("pct", "exec", vmid[3:], "--", "systemctl", "mask", "--runtime", unit)
    return ("pct", "exec", vmid[3:], "--", "systemctl", action, unit)


def atomic_state(path: Path, value: AdapterState) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(asdict(value), stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


class EvaluationLeaseAdapter:
    def __init__(self, state_path: Path, runner: Callable[[Sequence[str]], None], *,
                 allow_effects: bool = False):
        self.state_path = state_path
        self.lock_path = state_path.with_suffix(".lock")
        self.runner = runner
        self.allow_effects = allow_effects

    def _require_effects(self) -> None:
        if not self.allow_effects:
            raise AdapterError("evaluation effects are disabled")

    def _lock(self) -> None:
        try:
            self.lock_path.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise AdapterError("evaluation lease lock already exists") from exc

    def acquire(self, admission: Admission, *, now_epoch: int) -> dict[str, object]:
        validate_admission(admission, now_epoch=now_epoch)
        if self.state_path.exists() or self.lock_path.exists():
            raise AdapterError("durable evaluation state or lock already exists")
        if not self.allow_effects:
            return {"effects": "disabled", "state": LeaseState.READY.value,
                    "mode": "stream-a-endpoint-retaining-evaluation-v1"}
        self._lock()
        atomic_state(self.state_path, AdapterState(
            admission.lease_id, admission.generation, LeaseState.QUIESCING.value,
            admission.baseline, now_epoch, admission.hard_deadline_epoch,
            admission.restore_deadline_epoch,
        ))
        try:
            for target in QUIESCE_TARGETS:
                self.runner(consumer_command(target, "mask"))
                self.runner(consumer_command(target, "stop"))
        except Exception as exc:
            raise AdapterError("consumer quiescence is uncertain; recovery required") from exc
        return {"effects": "acquired-pre-run", "state": LeaseState.QUIESCING.value,
                "lease_id": admission.lease_id, "generation": admission.generation}

    def restore(self, *, lease_id: str, generation: int, restored: ProductionBaseline,
                backend_active: bool, endpoint_authenticated: bool,
                endpoint_idle: bool, gpu_holders: tuple[str, ...]) -> dict[str, object]:
        self._require_effects()
        if not self.state_path.exists() or not self.lock_path.exists():
            raise AdapterError("durable evaluation state and lock are required for restore")
        value = json.loads(self.state_path.read_text(encoding="utf-8"))
        if (value.get("lease_id"), value.get("generation"), value.get("phase")) != (
                lease_id, generation, LeaseState.RUNNING.value):
            raise AdapterError("restore identity or phase does not match active lease")
        expected = ProductionBaseline(
            tuple(tuple(item) for item in value["baseline"]["units"]),
            tuple(tuple(item) for item in value["baseline"]["timers"]),
        )
        atomic_state(self.state_path, AdapterState(
            lease_id, generation, LeaseState.RESTORING.value, expected,
            value["window_start_epoch"],
            value["hard_deadline_epoch"], value["restore_deadline_epoch"],
        ))
        try:
            for target, _state in expected.units + expected.timers:
                self.runner(consumer_command(target, "unmask"))
                self.runner(consumer_command(target, "start"))
            validate_restoration(
                restored=restored, expected=expected,
                backend_active=backend_active,
                endpoint_authenticated=endpoint_authenticated,
                endpoint_idle=endpoint_idle, gpu_holders=gpu_holders,
            )
        except Exception as exc:
            raise AdapterError("restoration is uncertain; durable lock retained") from exc
        self.state_path.unlink()
        self.lock_path.rmdir()
        return {"effects": "restored", "lease_id": lease_id, "generation": generation}

    def post_quiescence(self, *, observed_states: tuple[tuple[str, str], ...],
                        admission: Admission, backend_active: bool,
                        endpoint_authenticated: bool, endpoint_idle: bool,
                        gpu_holders: tuple[str, ...]) -> None:
        if not self.state_path.exists() or not self.lock_path.exists():
            raise AdapterError("durable evaluation state and lock are required")
        value = json.loads(self.state_path.read_text(encoding="utf-8"))
        if (value.get("lease_id"), value.get("generation"), value.get("phase")) != (
                admission.lease_id, admission.generation, LeaseState.QUIESCING.value):
            raise AdapterError("post-quiescence confirmation is not for the pre-run lease")
        validate_post_quiescence(
            admission, observed_states=observed_states,
            backend_active=backend_active,
            endpoint_authenticated=endpoint_authenticated,
            endpoint_idle=endpoint_idle, gpu_holders=gpu_holders,
        )
        atomic_state(self.state_path, AdapterState(
            admission.lease_id, admission.generation, LeaseState.RUNNING.value,
            admission.baseline, value["window_start_epoch"],
            value["hard_deadline_epoch"], value["restore_deadline_epoch"],
        ))

    def workload_allowed(self, *, lease_id: str, generation: int) -> bool:
        if not self.state_path.exists():
            return False
        value = json.loads(self.state_path.read_text(encoding="utf-8"))
        return (value.get("lease_id"), value.get("generation"), value.get("phase")) == (
            lease_id, generation, LeaseState.RUNNING.value)

