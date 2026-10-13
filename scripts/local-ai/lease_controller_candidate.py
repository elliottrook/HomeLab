"""Offline-installable Proxmox lease adapter candidate.

The adapter has real persistence and command boundaries, but defaults to a
fake command runner in tests. Deployment and enabling the watchdog remain
separate operations.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

from admission_state import AdmissionRecord, decode, encode
from lease_contract import LeaseReceipt, validate_receipt
from lease_watchdog import Observation, WatchdogState, decide
from trusted_observer import TrustedHostObserver


ALLOWLIST = (
    ("104", "aster-agent.service"),
    ("110", "aster-llama.service"),
    ("116", "aster-speech.service"),
)


@dataclass(frozen=True)
class CandidatePaths:
    root: Path

    @property
    def lock(self) -> Path:
        return self.root / "lease.lock"

    @property
    def state(self) -> Path:
        return self.root / "lease.json"

    @property
    def journal(self) -> Path:
        return self.root / "lease.jsonl"


def atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
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


def journal_event(path: Path, event: dict[str, object]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def command_for(vmid: str, unit: str, action: str) -> tuple[str, ...]:
    if (vmid, unit) not in ALLOWLIST or action not in {"start", "stop"}:
        raise ValueError("command is outside the lease allowlist")
    return ("pct", "exec", vmid, "--", "systemctl", action, unit)


class CandidateController:
    def __init__(self, paths: CandidatePaths, runner: Callable[[Sequence[str]], None], *, allow_effects: bool = False, observer: TrustedHostObserver | None = None):
        self.paths = paths
        self.runner = runner
        self.allow_effects = allow_effects
        self.observer = observer

    def _require_effect_authority(self) -> None:
        if not self.allow_effects:
            raise ValueError("candidate is advisory-only; live effects are disabled")

    def acquire(self, receipt: LeaseReceipt, observation: Observation, *, backup_receipt: str, active_services: tuple[tuple[str, str], ...] = ALLOWLIST) -> dict[str, object]:
        self._require_effect_authority()
        if any(service not in ALLOWLIST for service in active_services):
            raise ValueError("active service set is outside the lease allowlist")
        validate_receipt(receipt, now_minute=observation.now_minute, expected_backup_receipt=backup_receipt, watchdog_alive=observation.heartbeat_alive)
        if not observation.control_plane_healthy or not observation.production_services_healthy:
            raise ValueError("pre-acquire health gate failed")
        self.paths.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.paths.lock.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise ValueError("host lease lock already exists") from exc
        state = AdmissionRecord(
            lease_id=receipt.lease_id,
            generation=receipt.generation,
            state="leased",
            issued_minute=receipt.issued_minute,
            expires_minute=receipt.expires_minute,
            backup_receipt=receipt.backup_receipt,
            model_identity=receipt.model_identity,
            backend_identity=receipt.backend_identity,
            consumers_isolated=receipt.consumers_isolated,
            scheduled_work_quiesced=receipt.scheduled_work_quiesced,
            services=active_services,
        )
        atomic_write(self.paths.state, encode(state))
        stopped: list[tuple[str, str]] = []
        try:
            journal_event(self.paths.journal, {"event": "lease-acquired", "lease_id": receipt.lease_id, "generation": receipt.generation})
            for vmid, unit in active_services:
                journal_event(self.paths.journal, {"event": "stop-intent", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
                self.runner(command_for(vmid, unit, "stop"))
                stopped.append((vmid, unit))
                journal_event(self.paths.journal, {"event": "stop-observed", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
            return {"state": "leased", "lease_id": receipt.lease_id, "generation": receipt.generation}
        except Exception:
            journal_event(self.paths.journal, {"event": "stop-failed", "lease_id": receipt.lease_id, "generation": receipt.generation})
            for vmid, unit in reversed(stopped):
                journal_event(self.paths.journal, {"event": "restore-intent", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
                try:
                    self.runner(command_for(vmid, unit, "start"))
                    journal_event(self.paths.journal, {"event": "restore-observed", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
                except Exception:
                    journal_event(self.paths.journal, {"event": "restore-uncertain", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
            # Keep the lock and state: an uncertain effect requires review.
            raise

    def restore(self, receipt: LeaseReceipt, observation: Observation, *, backup_receipt: str) -> dict[str, object]:
        self._require_effect_authority()
        if not self.paths.lock.exists() or not self.paths.state.exists():
            raise ValueError("active lease state and lock are both required")
        persisted = decode(self.paths.state.read_text())
        if (persisted.lease_id, persisted.generation) != (receipt.lease_id, receipt.generation):
            raise ValueError("persisted lease identity does not match restore receipt")
        if not observation.control_plane_healthy:
            raise ValueError("control-plane postcheck is incomplete")
        if self.observer is None:
            raise ValueError("fixed trusted observer is required")
        events = []
        if self.paths.journal.exists():
            events = [json.loads(line) for line in self.paths.journal.read_text().splitlines() if line.strip()]
        current_events = []
        for event in events:
            if event.get("lease_id") != receipt.lease_id or event.get("generation") != receipt.generation:
                continue
            current_events.append(event)
        event_pairs = {
            kind: {(event.get("vmid"), event.get("unit")) for event in current_events if event.get("event") == kind}
            for kind in ("stop-intent", "stop-observed", "restore-intent", "restore-observed", "start-intent", "start-observed")
        }
        for intent, observed, label in (
            ("stop-intent", "stop-observed", "stop"),
            ("restore-intent", "restore-observed", "restore"),
            ("start-intent", "start-observed", "start"),
        ):
            if event_pairs[intent] - event_pairs[observed]:
                raise ValueError(f"uncertain prior {label} requires operator reconciliation")
        for vmid, unit in persisted.services:
            if (vmid, unit) in event_pairs["start-observed"] or self.observer.service_active(vmid, unit):
                journal_event(self.paths.journal, {"event": "start-skipped-active", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
                continue
            journal_event(self.paths.journal, {"event": "start-intent", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
            self.runner(command_for(vmid, unit, "start"))
            journal_event(self.paths.journal, {"event": "start-observed", "lease_id": receipt.lease_id, "generation": receipt.generation, "vmid": vmid, "unit": unit})
        fresh_observation = self.observer.collect(receipt.expires_minute)
        decision = decide(receipt, fresh_observation, backup_receipt=backup_receipt, current_state=WatchdogState.RESTORING)
        if decision.state != WatchdogState.READY:
            raise ValueError("post-restore checks are incomplete; lease retained")
        journal_event(self.paths.journal, {"event": "restore-validated", "lease_id": receipt.lease_id, "generation": receipt.generation})
        self.paths.state.unlink()
        self.paths.lock.rmdir()
        return {"state": "ready", "lease_id": receipt.lease_id, "generation": receipt.generation}
