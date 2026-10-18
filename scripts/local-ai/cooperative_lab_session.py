"""Source-bound, disabled-by-default controller for daytime lab hours."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Callable, Sequence
from zoneinfo import ZoneInfo

from application_b60_lease import ACCEPTED_BACKEND
from host_exclusion import host_exclusion

MAX_LAB_SECONDS = 45 * 60
DEFAULT_PILOT_SECONDS = 30 * 60
MIN_RESTORE_RESERVE_SECONDS = 15 * 60
MIN_NEWS_MARGIN_SECONDS = 5 * 60
LAB_TIMEZONE = ZoneInfo("America/Vancouver")
ALLOWED_CONSUMERS = (("104", "aster-agent.service"), ("116", "aster-speech.service"),
                     ("114", "news-aggregator-ingest.timer"), ("114", "news-aggregator-digest.timer"))


class LabSessionError(ValueError):
    pass


@dataclass(frozen=True)
class CooperativeLabPreflight:
    mode: str
    lease_id: str
    generation: int
    backup_receipt: str
    backend_identity: str
    gpu_visible: bool
    authentication_verified: bool
    source_verified: bool
    consumers_healthy: bool
    news_timers_active: bool
    deny_new_starts_supported: bool
    now_epoch: int
    session_start_epoch: int
    lab_end_epoch: int
    restore_deadline_epoch: int
    next_news_ingest_epoch: int
    direct_client_admission_enforced: bool


@dataclass(frozen=True)
class LabSessionPlan:
    mode: str
    lease_id: str
    generation: int
    lab_seconds: int
    restore_reserve_seconds: int
    preserve_backend: bool
    stop_commands: tuple[tuple[str, ...], ...]
    restore_commands: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class CooperativeLabPaths:
    root: Path

    @property
    def lock(self) -> Path:
        return self.root / "cooperative-lab.lock"

    @property
    def state(self) -> Path:
        return self.root / "cooperative-lab.json"

    @property
    def journal(self) -> Path:
        return self.root / "cooperative-lab.jsonl"


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def _journal(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _command(vmid: str, *args: str) -> tuple[str, ...]:
    return ("pct", "exec", vmid, "--", *args)


def _canonical_commands() -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]:
    stop = tuple(_command(v, "systemctl", "mask", "--runtime", "--now", u)
                 for v, u in ALLOWED_CONSUMERS)
    restore = tuple(command for v, u in reversed(ALLOWED_CONSUMERS)
                    for command in (_command(v, "systemctl", "unmask", "--runtime", u),
                                    _command(v, "systemctl", "start", u)))
    return stop, restore


def plan(preflight: CooperativeLabPreflight, *, lab_seconds: int = DEFAULT_PILOT_SECONDS) -> LabSessionPlan:
    """Validate a current source-bound reservation and return fixed commands."""
    if (preflight.mode != "cooperative-lab-v1" or not preflight.lease_id
            or type(preflight.generation) is not int or preflight.generation < 1
            or not preflight.backup_receipt):
        raise LabSessionError("source-bound lab identity is invalid")
    if (preflight.backend_identity != ACCEPTED_BACKEND or not preflight.gpu_visible
            or not preflight.authentication_verified or not preflight.source_verified
            or not preflight.consumers_healthy or not preflight.news_timers_active
            or not preflight.deny_new_starts_supported):
        raise LabSessionError("runtime source preflight is incomplete")
    if type(lab_seconds) is not int or not 1 <= lab_seconds <= MAX_LAB_SECONDS:
        raise LabSessionError("daytime lab budget is outside its bound")
    if not (preflight.now_epoch <= preflight.session_start_epoch < preflight.lab_end_epoch <= preflight.restore_deadline_epoch):
        raise LabSessionError("lab chronology is invalid")
    if preflight.lab_end_epoch - preflight.session_start_epoch != lab_seconds:
        raise LabSessionError("lab duration does not match the source-bound window")
    if preflight.restore_deadline_epoch - preflight.lab_end_epoch < MIN_RESTORE_RESERVE_SECONDS:
        raise LabSessionError("restoration reserve is insufficient")
    if preflight.restore_deadline_epoch + MIN_NEWS_MARGIN_SECONDS > preflight.next_news_ingest_epoch:
        raise LabSessionError("lab window overlaps the next News ingest")
    deadline = datetime.fromtimestamp(preflight.restore_deadline_epoch, LAB_TIMEZONE)
    if deadline.timetz().replace(tzinfo=None) > time(17, 15):
        raise LabSessionError("lab restore deadline crosses the news boundary")
    stop, restore = _canonical_commands()
    return LabSessionPlan(
        mode="cooperative-lab-v1", lease_id=preflight.lease_id, generation=preflight.generation,
        lab_seconds=lab_seconds, restore_reserve_seconds=MIN_RESTORE_RESERVE_SECONDS,
        preserve_backend=True,
        stop_commands=stop, restore_commands=restore,
    )


def require_usable_workload(preflight: CooperativeLabPreflight) -> None:
    """Separate gate for usable MacBook work; an observation is not enforcement."""
    if not preflight.direct_client_admission_enforced:
        raise LabSessionError("usable B60 workload is blocked: client admission is not enforced")


class CooperativeLabController:
    """Effectful candidate; disabled unless explicitly enabled by a platform wrapper."""

    def __init__(self, paths: CooperativeLabPaths, runner: Callable[[Sequence[str]], None], *,
                 allow_effects: bool = False,
                 observer: Callable[[str, Sequence[str]], bool] | None = None,
                 owner_id: str = ""):
        self.paths, self.runner, self.allow_effects, self.observer = paths, runner, allow_effects, observer
        self.owner_id = owner_id
        self._exclusion = None
        self._active = False

    def _require_effects(self) -> None:
        if not self.allow_effects:
            raise LabSessionError("cooperative lab controller is advisory-only; live effects are disabled")

    def begin(self, preflight: CooperativeLabPreflight, *, lab_seconds: int = DEFAULT_PILOT_SECONDS) -> LabSessionPlan:
        self._require_effects()
        if not self.owner_id:
            raise LabSessionError("durable owner identity is required")
        value = plan(preflight, lab_seconds=lab_seconds)
        self.paths.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.paths.state.exists() or self.paths.lock.exists():
            raise LabSessionError("existing cooperative lab state or lock is present")
        self._exclusion = host_exclusion(self.paths.root.parent)
        self._exclusion.__enter__()
        try:
            if self.paths.state.exists() or self.paths.lock.exists():
                raise LabSessionError("existing cooperative lab state or lock is present")
            self.paths.lock.mkdir(mode=0o700)
            state = {**asdict(value), "phase": "armed", "owner_id": self.owner_id,
                     "heartbeat_epoch": preflight.now_epoch,
                     "lab_end_epoch": preflight.lab_end_epoch,
                     "restore_deadline_epoch": preflight.restore_deadline_epoch}
            _atomic_write(self.paths.state, json.dumps(state, sort_keys=True) + "\n")
            self._active = True
            for command in value.stop_commands:
                unit = command[-1]
                _journal(self.paths.journal, {"event": "effect-intent", "lease_id": value.lease_id, "unit": unit})
                self.runner(command)
                if self.observer is None or not self.observer("mask", command):
                    raise LabSessionError(f"exact postcheck failed for {unit}")
                _journal(self.paths.journal, {"event": "effect-observed", "lease_id": value.lease_id, "unit": unit})
            _atomic_write(self.paths.state, json.dumps({**state, "phase": "leased"}, sort_keys=True) + "\n")
            return value
        except Exception:
            _journal(self.paths.journal, {"event": "effect-uncertain", "lease_id": value.lease_id})
            raise

    def heartbeat(self, now_epoch: int) -> None:
        """Refresh the durable owner heartbeat while the process holds the lock."""
        self._require_effects()
        if not self._active or not self.paths.state.exists():
            raise LabSessionError("no active cooperative lab lease")
        state = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if state.get("owner_id") != self.owner_id:
            raise LabSessionError("cooperative lab owner identity does not match")
        state["heartbeat_epoch"] = now_epoch
        _atomic_write(self.paths.state, json.dumps(state, sort_keys=True) + "\n")
        _journal(self.paths.journal, {"event": "heartbeat", "lease_id": state["lease_id"], "owner_id": self.owner_id})

    def require_work_window(self, now_epoch: int) -> None:
        """Trusted wrapper hook: stop the lab workload at the source-bound cutoff."""
        self._require_effects()
        if not self._active or not self.paths.state.exists():
            raise LabSessionError("no active cooperative lab lease")
        state = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if state.get("owner_id") != self.owner_id:
            raise LabSessionError("cooperative lab owner identity does not match")
        if now_epoch >= int(state["lab_end_epoch"]):
            _journal(self.paths.journal, {"event": "lab-cutoff", "lease_id": state["lease_id"]})
            raise LabSessionError("lab work window has ended; restore is required")

    def resume_existing(self, *, lease_id: str, generation: int) -> LabSessionPlan:
        """Reacquire a durable locked lease after the original owner process ended."""
        self._require_effects()
        if not self.owner_id or not self.paths.lock.exists() or not self.paths.state.exists():
            raise LabSessionError("durable cooperative lab state is unavailable")
        self._exclusion = host_exclusion(self.paths.root.parent)
        self._exclusion.__enter__()
        try:
            state = json.loads(self.paths.state.read_text(encoding="utf-8"))
            if (state.get("owner_id") != self.owner_id or state.get("lease_id") != lease_id
                    or int(state.get("generation", -1)) != generation):
                raise LabSessionError("durable cooperative lab identity does not match")
            stop, restore = _canonical_commands()
            if (tuple(tuple(x) for x in state.get("stop_commands", ())) != stop
                    or tuple(tuple(x) for x in state.get("restore_commands", ())) != restore):
                raise LabSessionError("durable cooperative lab command inventory is not canonical")
            self._active = True
            return LabSessionPlan(state["mode"], state["lease_id"], int(state["generation"]),
                                  int(state["lab_seconds"]), int(state["restore_reserve_seconds"]),
                                  bool(state["preserve_backend"]),
                                  tuple(tuple(x) for x in state["stop_commands"]),
                                  tuple(tuple(x) for x in state["restore_commands"]))
        except Exception:
            self._exclusion.__exit__(None, None, None)
            self._exclusion = None
            raise

    def restore(self, value: LabSessionPlan, *, now_epoch: int, owner_present: bool) -> None:
        self._require_effects()
        if not self._active or not owner_present:
            raise LabSessionError("owner presence and active lab lease are required for restore")
        state = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if (state.get("owner_id") != self.owner_id or state.get("lease_id") != value.lease_id
                or int(state.get("generation", -1)) != value.generation
                or state.get("phase") not in {"armed", "leased"}):
            raise LabSessionError("cooperative lab lease authority does not match")
        stop, restore = _canonical_commands()
        if value.stop_commands != stop or value.restore_commands != restore:
            raise LabSessionError("cooperative lab command inventory is not canonical")
        if now_epoch > int(state["restore_deadline_epoch"]):
            _journal(self.paths.journal, {"event": "restore-overdue", "lease_id": value.lease_id})
        for command in value.restore_commands:
            unit = command[-1]
            _journal(self.paths.journal, {"event": "restore-intent", "lease_id": value.lease_id, "unit": unit})
            try:
                self.runner(command)
                phase = "unmask" if "unmask" in command else "start"
                if self.observer is None or not self.observer(phase, command):
                    raise LabSessionError(f"exact postcheck failed for {unit}")
            except Exception:
                _journal(self.paths.journal, {"event": "restore-uncertain", "lease_id": value.lease_id, "unit": unit})
                raise
            _journal(self.paths.journal, {"event": "restore-observed", "lease_id": value.lease_id, "unit": unit})
        _journal(self.paths.journal, {"event": "restore-verified", "lease_id": value.lease_id})
        self.paths.state.unlink(missing_ok=True)
        self.paths.lock.rmdir()
        self._active = False
        self._exclusion.__exit__(None, None, None)
        self._exclusion = None
