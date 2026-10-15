"""Offline controller for the application-only B60 benchmark lease.

This controller deliberately has no command path for LXC110.  It persists a
small, secret-free application lease record before stopping the two allowed
production consumers and restores only those consumers after the sidecar
observation has been validated.  Live installation and enabling remain a
separate platform operation.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

from application_b60_lease import (
    ALLOWED_CONSUMER_SERVICES,
    APPLICATION_MODE,
    ApplicationLeaseReceipt,
    validate,
)


@dataclass(frozen=True)
class ApplicationLeaseState:
    mode: str
    lease_id: str
    generation: int
    backup_receipt: str
    services: tuple[tuple[str, str], ...]
    phase: str = "leased"
    armed: bool = False
    start_deadline_epoch: int | None = None
    restore_deadline_epoch: int | None = None


@dataclass(frozen=True)
class ApplicationPreLease:
    mode: str
    lease_id: str
    generation: int
    backup_receipt: str
    backend_identity: str
    llama_service_active: bool
    consumers_healthy: bool
    news_quiesced: bool
    now_epoch: int
    start_deadline_epoch: int
    restore_deadline_epoch: int


@dataclass(frozen=True)
class ApplicationPaths:
    root: Path

    @property
    def lock(self) -> Path:
        return self.root / "application-b60.lock"

    @property
    def state(self) -> Path:
        return self.root / "application-b60.json"

    @property
    def journal(self) -> Path:
        return self.root / "application-b60.jsonl"


def atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def command_for(vmid: str, unit: str, action: str) -> tuple[str, ...]:
    if (vmid, unit) not in ALLOWED_CONSUMER_SERVICES or action not in {"start", "stop"}:
        raise ValueError("application lease command is outside its consumer allowlist")
    return ("pct", "exec", vmid, "--", "systemctl", action, unit)


def _journal(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


class ApplicationB60Controller:
    def __init__(self, paths: ApplicationPaths, runner: Callable[[Sequence[str]], None], *, allow_effects: bool = False):
        self.paths = paths
        self.runner = runner
        self.allow_effects = allow_effects

    def _require_effect_authority(self) -> None:
        if not self.allow_effects:
            raise ValueError("application controller is advisory-only; live effects are disabled")

    def acquire(self, prelease: ApplicationPreLease) -> dict[str, object]:
        self._require_effect_authority()
        if (prelease.mode != APPLICATION_MODE or not prelease.backup_receipt
                or prelease.backup_receipt.startswith("full-stop:")
                or prelease.backend_identity != "llama.cpp b11429 SYCL/Level Zero"
                or not prelease.llama_service_active
                or not prelease.consumers_healthy or not prelease.news_quiesced
                or not prelease.now_epoch < prelease.start_deadline_epoch <= prelease.restore_deadline_epoch):
            raise ValueError("application pre-lease checkpoint is incomplete")
        self.paths.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.paths.lock.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise ValueError("application lease lock already exists") from exc
        state = ApplicationLeaseState(
            mode=prelease.mode,
            lease_id=prelease.lease_id,
            generation=prelease.generation,
            backup_receipt=prelease.backup_receipt,
            services=ALLOWED_CONSUMER_SERVICES,
            phase="armed",
            armed=True,
            start_deadline_epoch=prelease.start_deadline_epoch,
            restore_deadline_epoch=prelease.restore_deadline_epoch,
        )
        atomic_write(self.paths.state, json.dumps(asdict(state), sort_keys=True, separators=(",", ":")) + "\n")
        stopped: list[tuple[str, str]] = []
        try:
            _journal(self.paths.journal, {"event": "application-lease-acquired", "lease_id": prelease.lease_id, "generation": prelease.generation})
            for vmid, unit in ALLOWED_CONSUMER_SERVICES:
                _journal(self.paths.journal, {"event": "stop-intent", "lease_id": prelease.lease_id, "generation": prelease.generation, "vmid": vmid, "unit": unit})
                self.runner(command_for(vmid, unit, "stop"))
                stopped.append((vmid, unit))
                _journal(self.paths.journal, {"event": "stop-observed", "lease_id": prelease.lease_id, "generation": prelease.generation, "vmid": vmid, "unit": unit})
            return {"state": "application-leased", "mode": APPLICATION_MODE, "lease_id": prelease.lease_id, "generation": prelease.generation}
        except Exception:
            _journal(self.paths.journal, {"event": "stop-failed", "lease_id": prelease.lease_id, "generation": prelease.generation})
            for vmid, unit in reversed(stopped):
                _journal(self.paths.journal, {"event": "restore-intent", "lease_id": prelease.lease_id, "generation": prelease.generation, "vmid": vmid, "unit": unit})
                try:
                    self.runner(command_for(vmid, unit, "start"))
                    _journal(self.paths.journal, {"event": "restore-observed", "lease_id": prelease.lease_id, "generation": prelease.generation, "vmid": vmid, "unit": unit})
                except Exception:
                    _journal(self.paths.journal, {"event": "restore-uncertain", "lease_id": prelease.lease_id, "generation": prelease.generation, "vmid": vmid, "unit": unit})
            raise

    def mark_effect(self, effect: str, state: str, *, expected_lease_id: str, expected_generation: int) -> None:
        self._require_effect_authority()
        if effect not in {"key", "ingress"} or state not in {"intent", "observed"}:
            raise ValueError("unknown application effect transition")
        value = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if (value.get("mode"), value.get("lease_id"), value.get("generation"), value.get("armed")) != (APPLICATION_MODE, expected_lease_id, expected_generation, True):
            raise ValueError("application lease is not armed")
        effects = dict(value.get("effects", {}))
        current = effects.get(effect, "not-started")
        if state == "intent" and current != "not-started":
            raise ValueError("application effect already started or reconciled")
        if state == "observed" and current != "intent":
            raise ValueError("application effect observation has no matching intent")
        effects[effect] = state
        value["effects"] = effects
        atomic_write(self.paths.state, json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        _journal(self.paths.journal, {"event": f"{effect}-{state}", "lease_id": expected_lease_id, "generation": expected_generation})

    def admit_sidecar(self, receipt: ApplicationLeaseReceipt, *, expected_lease_id: str, expected_generation: int) -> dict[str, object]:
        self._require_effect_authority()
        if not self.paths.lock.exists() or not self.paths.state.exists():
            raise ValueError("application lease state and lock are both required")
        value = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if (value.get("mode"), value.get("lease_id"), value.get("generation"), value.get("phase")) != (APPLICATION_MODE, expected_lease_id, expected_generation, "armed"):
            raise ValueError("persisted application lease is not awaiting sidecar admission")
        validate(receipt, expected_lease_id=expected_lease_id, expected_generation=expected_generation)
        value["phase"] = "sidecar-admitted"
        atomic_write(self.paths.state, json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
        _journal(self.paths.journal, {"event": "sidecar-admitted", "lease_id": expected_lease_id, "generation": expected_generation})
        return {"state": "sidecar-admitted", "mode": APPLICATION_MODE, "lease_id": expected_lease_id, "generation": expected_generation}

    def restore(self, *args, **kwargs):
        raise ValueError("direct application restore is disabled; application watchdog recovery is required")
