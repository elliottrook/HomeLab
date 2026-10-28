"""Offline, disabled-by-default five-effect full-inference lab drain."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

from application_b60_lease import ACCEPTED_BACKEND
from cooperative_lab_session import (DEFAULT_PILOT_SECONDS, MIN_NEWS_MARGIN_SECONDS,
    MIN_RESTORE_RESERVE_SECONDS, _atomic_write, _journal)
from host_exclusion import host_exclusion

MAX_DRAIN_SECONDS = 45 * 60
FULL_DRAIN_CONSUMERS = (("104", "aster-agent.service"), ("116", "aster-speech.service"),
                        ("110", "aster-llama.service"),
                        ("114", "news-aggregator-ingest.timer"),
                        ("114", "news-aggregator-digest.timer"),
                        ("116", "epub-narration-worker.timer"),
                        ("116", "epub-narration-worker.service"))


class FullDrainError(ValueError):
    pass


@dataclass(frozen=True)
class FullDrainPreflight:
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
    host_driver_verified: bool
    rollback_vm_safe: bool
    accepted_baseline_verified: bool
    admin_path_verified: bool
    now_epoch: int
    session_start_epoch: int
    lab_end_epoch: int
    restore_deadline_epoch: int
    next_news_ingest_epoch: int


@dataclass(frozen=True)
class FullDrainPlan:
    mode: str
    lease_id: str
    generation: int
    lab_seconds: int
    restore_reserve_seconds: int
    drain_commands: tuple[tuple[str, ...], ...]
    restore_commands: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class FullDrainPaths:
    root: Path

    @property
    def lock(self) -> Path:
        return self.root / "full-inference-drain.lock"

    @property
    def state(self) -> Path:
        return self.root / "full-inference-drain.json"

    @property
    def journal(self) -> Path:
        return self.root / "full-inference-drain.jsonl"


def _command(vmid: str, *args: str) -> tuple[str, ...]:
    return ("pct", "exec", vmid, "--", *args)


FULL_WARMUP_COMMAND = _command("110", "/usr/local/sbin/aster-llama-production-auth-probe")


def canonical_commands() -> tuple[tuple[tuple[str, ...], ...], tuple[tuple[str, ...], ...]]:
    drain = tuple(_command(v, "systemctl", "mask", "--runtime", "--now", u)
                  for v, u in FULL_DRAIN_CONSUMERS[:-1]) + (
        _command("116", "systemctl", "stop", "epub-narration-worker.service"),
    )
    restore = (
        _command("110", "systemctl", "unmask", "--runtime", "aster-llama.service"),
        _command("116", "systemctl", "unmask", "--runtime", "aster-speech.service"),
        _command("104", "systemctl", "unmask", "--runtime", "aster-agent.service"),
        _command("110", "systemctl", "start", "aster-llama.service"),
        FULL_WARMUP_COMMAND,
        _command("116", "systemctl", "start", "aster-speech.service"),
        _command("104", "systemctl", "start", "aster-agent.service"),
        _command("114", "systemctl", "unmask", "--runtime", "news-aggregator-ingest.timer"),
        _command("114", "systemctl", "start", "news-aggregator-ingest.timer"),
        _command("114", "systemctl", "unmask", "--runtime", "news-aggregator-digest.timer"),
        _command("114", "systemctl", "start", "news-aggregator-digest.timer"),
        _command("116", "systemctl", "unmask", "--runtime", "epub-narration-worker.timer"),
        _command("116", "systemctl", "start", "epub-narration-worker.timer"),
        _command("116", "systemctl", "start", "--no-block", "epub-narration-worker.service"),
    )
    return drain, restore


def plan(preflight: FullDrainPreflight, *, lab_seconds: int = DEFAULT_PILOT_SECONDS,
         allow_news_overlap: bool = False) -> FullDrainPlan:
    if (preflight.mode != "full-inference-drain-v1" or not preflight.lease_id
            or type(preflight.generation) is not int or preflight.generation < 1
            or not preflight.backup_receipt):
        raise FullDrainError("full-drain source identity is invalid")
    if (preflight.backend_identity != ACCEPTED_BACKEND or
            not all((preflight.gpu_visible, preflight.authentication_verified,
                     preflight.source_verified, preflight.consumers_healthy,
                     preflight.news_timers_active, preflight.host_driver_verified,
                     preflight.rollback_vm_safe, preflight.accepted_baseline_verified,
                     preflight.admin_path_verified))):
        raise FullDrainError("full-drain source preflight is incomplete")
    if type(lab_seconds) is not int or not 1 <= lab_seconds <= MAX_DRAIN_SECONDS:
        raise FullDrainError("full-drain budget is outside its bound")
    if not (preflight.now_epoch <= preflight.session_start_epoch < preflight.lab_end_epoch
            <= preflight.restore_deadline_epoch):
        raise FullDrainError("full-drain chronology is invalid")
    if preflight.lab_end_epoch - preflight.session_start_epoch != lab_seconds:
        raise FullDrainError("full-drain duration does not match its window")
    if preflight.restore_deadline_epoch - preflight.lab_end_epoch < MIN_RESTORE_RESERVE_SECONDS:
        raise FullDrainError("full-drain restoration reserve is insufficient")
    if (not allow_news_overlap and
            preflight.restore_deadline_epoch + MIN_NEWS_MARGIN_SECONDS > preflight.next_news_ingest_epoch):
        raise FullDrainError("full-drain window overlaps the next News ingest")
    drain, restore = canonical_commands()
    return FullDrainPlan("full-inference-drain-v1", preflight.lease_id, preflight.generation,
                         lab_seconds, MIN_RESTORE_RESERVE_SECONDS, drain, restore)


class FullInferenceDrainController:
    """Fixed five-effect controller; live effects are disabled by default."""

    def __init__(self, paths: FullDrainPaths, runner: Callable[[Sequence[str]], None], *,
                 observer: Callable[[str, Sequence[str]], bool] | None = None,
                 validator: Callable[[], bool] | None = None,
                 owner_id: str = "", allow_effects: bool = False,
                 allow_news_overlap: bool = False):
        self.paths, self.runner, self.observer, self.validator = paths, runner, observer, validator
        self.owner_id, self.allow_effects = owner_id, allow_effects
        self.allow_news_overlap = allow_news_overlap
        self._exclusion = None
        self._active = False

    def _require_effects(self) -> None:
        if not self.allow_effects:
            raise FullDrainError("full-drain controller is advisory-only; live effects are disabled")

    def begin(self, preflight: FullDrainPreflight, *, lab_seconds: int = DEFAULT_PILOT_SECONDS) -> FullDrainPlan:
        self._require_effects()
        if not self.owner_id:
            raise FullDrainError("full-drain owner identity is required")
        value = plan(preflight, lab_seconds=lab_seconds,
                     allow_news_overlap=self.allow_news_overlap)
        self.paths.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._exclusion = host_exclusion(self.paths.root)
        self._exclusion.__enter__()
        try:
            if self.paths.state.exists() or self.paths.lock.exists():
                raise FullDrainError("existing full-drain state or lock is present")
            self.paths.lock.mkdir(mode=0o700)
            state = {**asdict(value), "phase": "armed", "owner_id": self.owner_id,
                     "heartbeat_epoch": preflight.now_epoch,
                     "lab_end_epoch": preflight.lab_end_epoch,
                     "restore_deadline_epoch": preflight.restore_deadline_epoch}
            _atomic_write(self.paths.state, json.dumps(state, sort_keys=True) + "\n")
            self._active = True
            for command in value.drain_commands:
                self._effect("drain", command, value.lease_id)
            _atomic_write(self.paths.state, json.dumps({**state, "phase": "drained"}, sort_keys=True) + "\n")
            return value
        except Exception:
            _journal(self.paths.journal, {"event": "drain-uncertain", "lease_id": value.lease_id})
            raise

    def _effect(self, phase: str, command: Sequence[str], lease_id: str) -> None:
        unit = command[-1]
        _journal(self.paths.journal, {"event": f"{phase}-intent", "lease_id": lease_id,
                                      "unit": unit, "command": list(command)})
        try:
            result = self.runner(command)
            if (isinstance(result, tuple) and len(result) == 2
                    and type(result[0]) is int and result[0] != 0):
                raise FullDrainError(f"fixed {phase} command returned nonzero status for {unit}")
            probe_phase = ("mask" if "mask" in command else "stop") if phase == "drain" else (
                "warmup" if tuple(command) == FULL_WARMUP_COMMAND else
                ("unmask" if "unmask" in command else "start"))
            if self.observer is None or not self.observer(probe_phase, command):
                raise FullDrainError(f"exact {phase} postcheck failed for {unit}")
        except Exception:
            _journal(self.paths.journal, {"event": f"{phase}-uncertain", "lease_id": lease_id, "unit": unit})
            raise
        _journal(self.paths.journal, {"event": f"{phase}-observed", "lease_id": lease_id,
                                      "unit": unit, "command": list(command)})

    def heartbeat(self, now_epoch: int) -> None:
        self._require_effects()
        if not self._active or not self.paths.state.exists():
            raise FullDrainError("no active full-drain lease")
        state = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if state.get("owner_id") != self.owner_id:
            raise FullDrainError("full-drain owner identity does not match")
        state["heartbeat_epoch"] = now_epoch
        _atomic_write(self.paths.state, json.dumps(state, sort_keys=True) + "\n")
        _journal(self.paths.journal, {"event": "heartbeat", "lease_id": state["lease_id"]})

    def require_work_window(self, now_epoch: int) -> None:
        self._require_effects()
        if not self._active or not self.paths.state.exists():
            raise FullDrainError("no active full-drain lease")
        state = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if now_epoch >= int(state["lab_end_epoch"]):
            _journal(self.paths.journal, {"event": "lab-cutoff", "lease_id": state["lease_id"]})
            raise FullDrainError("full-drain lab window has ended; restore is required")

    def resume_existing(self, *, lease_id: str, generation: int) -> FullDrainPlan:
        self._require_effects()
        if not self.owner_id or not self.paths.lock.exists() or not self.paths.state.exists():
            raise FullDrainError("durable full-drain state is unavailable")
        self._exclusion = host_exclusion(self.paths.root)
        self._exclusion.__enter__()
        try:
            state = json.loads(self.paths.state.read_text(encoding="utf-8"))
            drain, restore = canonical_commands()
            if (state.get("owner_id") != self.owner_id or state.get("lease_id") != lease_id
                    or int(state.get("generation", -1)) != generation
                    or tuple(tuple(x) for x in state.get("drain_commands", ())) != drain
                    or tuple(tuple(x) for x in state.get("restore_commands", ())) != restore):
                raise FullDrainError("durable full-drain identity or inventory does not match")
            self._active = True
            return FullDrainPlan(state["mode"], state["lease_id"], int(state["generation"]),
                                 int(state["lab_seconds"]), int(state["restore_reserve_seconds"]),
                                 tuple(tuple(x) for x in state["drain_commands"]),
                                 tuple(tuple(x) for x in state["restore_commands"]))
        except Exception:
            self._exclusion.__exit__(None, None, None)
            self._exclusion = None
            raise

    def restore(self, value: FullDrainPlan, *, now_epoch: int, owner_present: bool) -> None:
        self._require_effects()
        if not self._active or not owner_present:
            raise FullDrainError("owner presence and active full-drain lease are required")
        state = json.loads(self.paths.state.read_text(encoding="utf-8"))
        drain, restore = canonical_commands()
        if (state.get("owner_id") != self.owner_id or state.get("lease_id") != value.lease_id
                or int(state.get("generation", -1)) != value.generation
                or state.get("phase") not in {"armed", "drained"}
                or value.drain_commands != drain or value.restore_commands != restore):
            raise FullDrainError("full-drain authority or command inventory does not match")
        if now_epoch > int(state["restore_deadline_epoch"]):
            _journal(self.paths.journal, {"event": "restore-overdue", "lease_id": value.lease_id})
        observed = {tuple(event.get("command", ())) for event in
                    (_read_journal(self.paths.journal))
                    if event.get("event") == "restore-observed"}
        for command in value.restore_commands:
            phase = ("warmup" if tuple(command) == FULL_WARMUP_COMMAND else
                     ("unmask" if "unmask" in command else "start"))
            if tuple(command) in observed:
                if self.observer is not None and self.observer(phase, command):
                    _journal(self.paths.journal, {"event": "restore-skipped-verified",
                                                  "lease_id": value.lease_id, "unit": command[-1],
                                                  "command": list(command)})
                    continue
                _journal(self.paths.journal, {"event": "restore-replay-required",
                                              "lease_id": value.lease_id, "unit": command[-1],
                                              "command": list(command)})
            self._effect("restore", command, value.lease_id)
        if self.validator is None or not self.validator():
            _journal(self.paths.journal, {"event": "restore-uncertain", "lease_id": value.lease_id})
            raise FullDrainError("final full-drain restoration validation failed; retain lock")
        _journal(self.paths.journal, {"event": "restore-verified", "lease_id": value.lease_id})
        self.paths.state.unlink(missing_ok=True)
        self.paths.lock.rmdir()
        self._active = False
        self._exclusion.__exit__(None, None, None)
        self._exclusion = None


def _read_journal(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
