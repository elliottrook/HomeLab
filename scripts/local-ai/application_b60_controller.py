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

    def acquire(self, receipt: ApplicationLeaseReceipt, *, expected_lease_id: str, expected_generation: int) -> dict[str, object]:
        self._require_effect_authority()
        validate(receipt, expected_lease_id=expected_lease_id, expected_generation=expected_generation)
        self.paths.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.paths.lock.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise ValueError("application lease lock already exists") from exc
        state = ApplicationLeaseState(
            mode=receipt.mode,
            lease_id=receipt.lease_id,
            generation=receipt.generation,
            backup_receipt=receipt.backup_receipt,
            services=ALLOWED_CONSUMER_SERVICES,
        )
        atomic_write(self.paths.state, json.dumps(asdict(state), sort_keys=True, separators=(",", ":")) + "\n")
        stopped: list[tuple[str, str]] = []
        try:
            _journal(self.paths.journal, {"event": "application-lease-acquired", "lease_id": receipt.lease_id, "generation": receipt.generation})
            for vmid, unit in ALLOWED_CONSUMER_SERVICES:
                _journal(self.paths.journal, {"event": "stop-intent", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
                self.runner(command_for(vmid, unit, "stop"))
                stopped.append((vmid, unit))
                _journal(self.paths.journal, {"event": "stop-observed", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
            return {"state": "application-leased", "mode": APPLICATION_MODE, "lease_id": receipt.lease_id, "generation": receipt.generation}
        except Exception:
            _journal(self.paths.journal, {"event": "stop-failed", "lease_id": receipt.lease_id, "generation": receipt.generation})
            for vmid, unit in reversed(stopped):
                _journal(self.paths.journal, {"event": "restore-intent", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
                try:
                    self.runner(command_for(vmid, unit, "start"))
                    _journal(self.paths.journal, {"event": "restore-observed", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
                except Exception:
                    _journal(self.paths.journal, {"event": "restore-uncertain", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
            raise

    def restore(self, receipt: ApplicationLeaseReceipt, *, expected_lease_id: str, expected_generation: int) -> dict[str, object]:
        self._require_effect_authority()
        if not self.paths.lock.exists() or not self.paths.state.exists():
            raise ValueError("application lease state and lock are both required")
        value = json.loads(self.paths.state.read_text(encoding="utf-8"))
        if value.get("mode") != APPLICATION_MODE or value.get("lease_id") != expected_lease_id or value.get("generation") != expected_generation:
            raise ValueError("persisted application lease identity does not match")
        validate(receipt, expected_lease_id=expected_lease_id, expected_generation=expected_generation)
        for vmid, unit in ALLOWED_CONSUMER_SERVICES:
            _journal(self.paths.journal, {"event": "start-intent", "lease_id": expected_lease_id, "generation": expected_generation, "vmid": vmid, "unit": unit})
            self.runner(command_for(vmid, unit, "start"))
            _journal(self.paths.journal, {"event": "start-observed", "lease_id": expected_lease_id, "generation": expected_generation, "vmid": vmid, "unit": unit})
        _journal(self.paths.journal, {"event": "application-restore-validated", "lease_id": expected_lease_id, "generation": expected_generation})
        self.paths.state.unlink()
        self.paths.lock.rmdir()
        return {"state": "ready", "mode": APPLICATION_MODE, "lease_id": expected_lease_id, "generation": expected_generation}
