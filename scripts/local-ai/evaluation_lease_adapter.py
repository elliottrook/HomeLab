"""Effect adapter for the Stream A endpoint-retaining evaluation lease.

The adapter is deliberately disabled unless a future production constructor
supplies ``allow_effects=True``.  Its command surface is allowlisted to the
four registered consumers; the accepted llama service is never a command
target.  Recovery retains durable state and the lock on any uncertainty.
"""

from __future__ import annotations

import hashlib
import fcntl
import json
import os
import stat
import tempfile
from contextlib import contextmanager
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
    workload,
    WorkloadOutcome,
    validate_outcome,
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
    heartbeat_epoch: int
    hard_deadline_epoch: int
    restore_deadline_epoch: int
    next_workload: str | None
    in_flight_workload: str | None
    completed_outcomes: tuple[tuple[str, str, str], ...]


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


def read_state(path: Path, *, expected_lease_id: str | None = None,
               expected_generation: int | None = None) -> AdapterState:
    """Read one owner/mode-checked descriptor without reopening its pathname."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise AdapterError("evaluation state descriptor cannot be opened safely") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise AdapterError("evaluation state custody is weak")
        def unique_pairs(pairs):
            result = {}
            for key, item in pairs:
                if key in result:
                    raise AdapterError("evaluation state contains duplicate JSON keys")
                result[key] = item
            return result
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            value = json.load(stream, object_pairs_hook=unique_pairs)
    finally:
        if fd != -1:
            os.close(fd)
    if not isinstance(value, dict) or set(value) != {
            "lease_id", "generation", "phase", "baseline", "window_start_epoch",
            "heartbeat_epoch", "hard_deadline_epoch", "restore_deadline_epoch",
            "next_workload", "in_flight_workload", "completed_outcomes"}:
        raise AdapterError("evaluation state key set is not exact")
    if (not isinstance(value["lease_id"], str) or type(value["generation"]) is not int
            or not isinstance(value["phase"], str)
            or any(type(value[key]) is not int for key in (
                "window_start_epoch", "heartbeat_epoch", "hard_deadline_epoch",
                "restore_deadline_epoch"))):
        raise AdapterError("evaluation state types are invalid")
    try:
        state = AdapterState(
            value["lease_id"], value["generation"], value["phase"],
            ProductionBaseline(
                tuple(tuple(item) for item in value["baseline"]["units"]),
                tuple(tuple(item) for item in value["baseline"]["timers"]),
            ), value["window_start_epoch"], value["heartbeat_epoch"],
            value["hard_deadline_epoch"], value["restore_deadline_epoch"],
            value["next_workload"], value["in_flight_workload"],
            tuple(tuple(item) for item in value["completed_outcomes"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AdapterError("evaluation state schema is malformed") from exc
    validate_baseline(state.baseline)
    if state.next_workload not in {None, "d4-candidate-g", "m3-nlu-calibration"}:
        raise AdapterError("evaluation state next workload is invalid")
    if state.in_flight_workload not in {None, "d4-candidate-g", "m3-nlu-calibration"}:
        raise AdapterError("evaluation state in-flight workload is invalid")
    rows = state.completed_outcomes
    if (len(rows) > 2
            or tuple(row[0] for row in rows)
            not in {(), ("d4-candidate-g",), ("d4-candidate-g", "m3-nlu-calibration")}
            or any(len(row) != 3 or not isinstance(row[0], str)
                   or not isinstance(row[1], str) or not isinstance(row[2], str)
                   or len(row[1]) != 64 or len(row[2]) != 64
                   or any(character not in "0123456789abcdef" for character in row[1] + row[2])
                   for row in rows)):
        raise AdapterError("evaluation state outcome progression is invalid")
    expected_next = ("d4-candidate-g" if not rows
                     else "m3-nlu-calibration" if len(rows) == 1 else None)
    if state.next_workload != expected_next:
        raise AdapterError("evaluation state next workload is incoherent")
    if state.in_flight_workload not in {None, expected_next}:
        raise AdapterError("evaluation state in-flight workload is incoherent")
    if (expected_lease_id is not None and state.lease_id != expected_lease_id) or (
            expected_generation is not None and state.generation != expected_generation):
        raise AdapterError("evaluation state identity does not match")
    return state


class EvaluationLeaseAdapter:
    def __init__(self, state_path: Path, runner: Callable[[Sequence[str]], None], *,
                 allow_effects: bool = False):
        self.state_path = state_path
        self.lock_path = state_path.with_suffix(".lock")
        self.operation_lock_path = state_path.with_suffix(".operation.lock")
        self.runner = runner
        self.allow_effects = allow_effects

    @contextmanager
    def _operation_guard(self):
        fd = os.open(self.operation_lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(fd)
            raise AdapterError("evaluation operation is already in progress") from exc
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

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
            admission.baseline, now_epoch, now_epoch, admission.hard_deadline_epoch,
            admission.restore_deadline_epoch, "d4-candidate-g", None, (),
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
                endpoint_idle: bool, gpu_holders: tuple[str, ...],
                recovery: bool = False) -> dict[str, object]:
        self._require_effects()
        with self._operation_guard():
            return self._restore_locked(
                lease_id=lease_id, generation=generation, restored=restored,
                backend_active=backend_active,
                endpoint_authenticated=endpoint_authenticated,
                endpoint_idle=endpoint_idle, gpu_holders=gpu_holders,
                recovery=recovery,
            )

    def _restore_locked(self, *, lease_id: str, generation: int,
                        restored: ProductionBaseline, backend_active: bool,
                        endpoint_authenticated: bool, endpoint_idle: bool,
                        gpu_holders: tuple[str, ...], recovery: bool) -> dict[str, object]:
        if not self.state_path.exists() or not self.lock_path.exists():
            raise AdapterError("durable evaluation state and lock are required for restore")
        state = read_state(self.state_path, expected_lease_id=lease_id,
                           expected_generation=generation)
        if state.phase not in {LeaseState.QUIESCING.value, LeaseState.RUNNING.value,
                               LeaseState.RESTORING.value}:
            raise AdapterError("restore phase is not recoverable")
        if (state.phase == LeaseState.RUNNING.value and not recovery
                and (state.next_workload is not None or state.in_flight_workload is not None
                     or len(state.completed_outcomes) != 2)):
            raise AdapterError("normal restoration requires terminal D4 and M3 outcomes")
        expected = state.baseline
        atomic_state(self.state_path, AdapterState(
            lease_id, generation, LeaseState.RESTORING.value, expected,
            state.window_start_epoch, state.heartbeat_epoch,
            state.hard_deadline_epoch, state.restore_deadline_epoch,
            state.next_workload, state.in_flight_workload, state.completed_outcomes,
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
                        gpu_holders: tuple[str, ...], now_epoch: int,
                        heartbeat_timeout: int) -> None:
        with self._operation_guard():
            self._post_quiescence_locked(
                observed_states=observed_states, admission=admission,
                backend_active=backend_active,
                endpoint_authenticated=endpoint_authenticated,
                endpoint_idle=endpoint_idle, gpu_holders=gpu_holders,
                now_epoch=now_epoch, heartbeat_timeout=heartbeat_timeout,
            )

    def _post_quiescence_locked(self, *, observed_states: tuple[tuple[str, str], ...],
                                admission: Admission, backend_active: bool,
                                endpoint_authenticated: bool, endpoint_idle: bool,
                                gpu_holders: tuple[str, ...], now_epoch: int,
                                heartbeat_timeout: int) -> None:
        if not self.state_path.exists() or not self.lock_path.exists():
            raise AdapterError("durable evaluation state and lock are required")
        state = read_state(self.state_path, expected_lease_id=admission.lease_id,
                           expected_generation=admission.generation)
        if state.phase != LeaseState.QUIESCING.value:
            raise AdapterError("post-quiescence confirmation is not for the pre-run lease")
        if (now_epoch < state.window_start_epoch
                or now_epoch >= state.hard_deadline_epoch
                or state.heartbeat_epoch > now_epoch
                or now_epoch - state.heartbeat_epoch > heartbeat_timeout):
            raise AdapterError("post-quiescence deadline or heartbeat gate failed")
        validate_post_quiescence(
            admission, observed_states=observed_states,
            backend_active=backend_active,
            endpoint_authenticated=endpoint_authenticated,
            endpoint_idle=endpoint_idle, gpu_holders=gpu_holders,
        )
        atomic_state(self.state_path, AdapterState(
            admission.lease_id, admission.generation, LeaseState.RUNNING.value,
            admission.baseline, state.window_start_epoch, now_epoch,
            state.hard_deadline_epoch, state.restore_deadline_epoch,
            state.next_workload, state.in_flight_workload, state.completed_outcomes,
        ))

    def heartbeat(self, *, lease_id: str, generation: int, now_epoch: int) -> None:
        with self._operation_guard():
            self._heartbeat_locked(lease_id=lease_id, generation=generation,
                                   now_epoch=now_epoch)

    def _heartbeat_locked(self, *, lease_id: str, generation: int,
                          now_epoch: int) -> None:
        state = read_state(self.state_path, expected_lease_id=lease_id,
                           expected_generation=generation)
        if state.phase not in {LeaseState.QUIESCING.value, LeaseState.RUNNING.value,
                               LeaseState.RESTORING.value}:
            raise AdapterError("heartbeat phase is not active")
        atomic_state(self.state_path, AdapterState(
            state.lease_id, state.generation, state.phase, state.baseline,
            state.window_start_epoch, now_epoch, state.hard_deadline_epoch,
            state.restore_deadline_epoch, state.next_workload,
            state.in_flight_workload, state.completed_outcomes,
        ))

    def workload_allowed(self, *, lease_id: str, generation: int, workload_name: str,
                         now_epoch: int, heartbeat_timeout: int) -> bool:
        if not self.state_path.exists():
            return False
        state = read_state(self.state_path, expected_lease_id=lease_id,
                           expected_generation=generation)
        if state.phase != LeaseState.RUNNING.value or state.in_flight_workload is not None:
            return False
        if state.next_workload != workload_name:
            return False
        if (now_epoch < state.window_start_epoch
                or now_epoch >= state.hard_deadline_epoch
                or state.heartbeat_epoch > now_epoch
                or now_epoch - state.heartbeat_epoch > heartbeat_timeout):
            return False
        return state.hard_deadline_epoch - now_epoch >= workload(workload_name).max_seconds

    def start_workload(self, *, lease_id: str, generation: int, workload_name: str,
                       now_epoch: int, heartbeat_timeout: int) -> None:
        with self._operation_guard():
            if not self.workload_allowed(
                    lease_id=lease_id, generation=generation, workload_name=workload_name,
                    now_epoch=now_epoch, heartbeat_timeout=heartbeat_timeout):
                raise AdapterError("workload start is not admitted by the durable sequence")
            state = read_state(self.state_path, expected_lease_id=lease_id,
                               expected_generation=generation)
            atomic_state(self.state_path, AdapterState(
                state.lease_id, state.generation, state.phase, state.baseline,
                state.window_start_epoch, now_epoch, state.hard_deadline_epoch,
                state.restore_deadline_epoch, state.next_workload, workload_name,
                state.completed_outcomes,
            ))

    def record_outcome(self, outcome: WorkloadOutcome, *, now_epoch: int,
                       heartbeat_timeout: int) -> None:
        with self._operation_guard():
            self._record_outcome_locked(outcome, now_epoch=now_epoch,
                                        heartbeat_timeout=heartbeat_timeout)

    def _record_outcome_locked(self, outcome: WorkloadOutcome, *, now_epoch: int,
                               heartbeat_timeout: int) -> None:
        state = read_state(self.state_path, expected_lease_id=outcome.lease_id,
                           expected_generation=outcome.generation)
        if state.phase != LeaseState.RUNNING.value or state.in_flight_workload != outcome.name:
            raise AdapterError("outcome does not match the one in-flight workload")
        validate_outcome(outcome, expected=workload(outcome.name),
                         lease_id=outcome.lease_id, generation=outcome.generation)
        if now_epoch < state.window_start_epoch or now_epoch >= state.hard_deadline_epoch:
            raise AdapterError("outcome arrived outside the effect window")
        if state.heartbeat_epoch > now_epoch or now_epoch - state.heartbeat_epoch > heartbeat_timeout:
            raise AdapterError("outcome heartbeat is stale or from the future")
        names = tuple(row[0] for row in state.completed_outcomes)
        if outcome.name != ("d4-candidate-g" if names == () else "m3-nlu-calibration"):
            raise AdapterError("outcome is not the next frozen workload")
        completed = state.completed_outcomes + ((outcome.name, outcome.journal_digest, outcome.result_digest),)
        next_name = "m3-nlu-calibration" if outcome.name == "d4-candidate-g" else None
        atomic_state(self.state_path, AdapterState(
            state.lease_id, state.generation, state.phase, state.baseline,
            state.window_start_epoch, now_epoch, state.hard_deadline_epoch,
            state.restore_deadline_epoch, next_name, None, completed,
        ))

