"""Fail-closed recovery candidate for application-only B60 effects.

The whole-host watchdog cannot recover an application lease because that lease
owns a sidecar, a temporary LXC110 ingress policy and a temporary backend key.
This candidate deliberately restores those effects before restarting consumers.
It is offline-only until the fixed host helper commands and observer are
installed and independently validated.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


APPLICATION_MODE = "application-b60-exclusive-v1"
STATE_NAME = "application-b60.json"
LOCK_NAME = "application-b60.lock"
INGRESS_CHECKPOINT = "/var/lib/local-ai-lab/application-b60/llama-ingress-policy.checkpoint"
KEY_CHECKPOINT = "/var/lib/local-ai-lab/application-b60/aster-llama-api-keys.checkpoint"


@dataclass(frozen=True)
class RecoveryObservation:
    sidecar_stopped: bool
    ingress_restored: bool
    test_key_removed: bool
    production_auth_ok: bool
    wrong_key_denied: bool
    consumers_healthy: bool


def fixed_command(kind: str) -> tuple[str, ...]:
    commands = {
        "stop-sidecar": ("pct", "exec", "104", "--", "systemctl", "stop", "aster-a1-test.service"),
        "restore-ingress": ("pct", "exec", "110", "--", "/usr/local/sbin/aster-llama-ingress-restore", "--checkpoint", INGRESS_CHECKPOINT),
        "remove-test-key": ("pct", "exec", "110", "--", "/usr/local/sbin/aster-llama-test-key-remove", "--checkpoint", KEY_CHECKPOINT),
        "reload-backend": ("pct", "exec", "110", "--", "systemctl", "restart", "aster-llama.service"),
        "start-aster": ("pct", "exec", "104", "--", "systemctl", "start", "aster-agent.service"),
        "start-speech": ("pct", "exec", "116", "--", "systemctl", "start", "aster-speech.service"),
    }
    try:
        return commands[kind]
    except KeyError as exc:
        raise ValueError("unknown application recovery command") from exc


class ApplicationB60Watchdog:
    def __init__(self, state_dir: Path, runner: Callable[[Sequence[str]], None], observer, *, allow_effects: bool = False):
        self.state_dir = state_dir
        self.runner = runner
        self.observer = observer
        self.allow_effects = allow_effects

    def recover(self, *, lease_id: str, generation: int, now_minute: int) -> dict[str, object]:
        if not self.allow_effects:
            raise ValueError("application watchdog is advisory-only; live effects are disabled")
        state = self.state_dir / STATE_NAME
        lock = self.state_dir / LOCK_NAME
        if not state.exists() or not lock.exists():
            raise ValueError("application lease state and lock are required")
        record = json.loads(state.read_text(encoding="utf-8"))
        if (record.get("mode"), record.get("lease_id"), record.get("generation")) != (APPLICATION_MODE, lease_id, generation):
            raise ValueError("application lease identity does not match")
        if (record.get("armed") is not True
                or not isinstance(record.get("start_deadline_minute"), int)
                or not isinstance(record.get("restore_deadline_minute"), int)):
            raise ValueError("application watchdog is not armed")
        overdue = now_minute > record["restore_deadline_minute"]
        if overdue:
            self._journal_status(lease_id, generation, "recovery-overdue")

        self._step(lease_id, generation, "stop-sidecar", lambda: self.observer.sidecar_stopped())
        self._step(lease_id, generation, "restore-ingress", lambda: self.observer.ingress_restored())
        self._step(lease_id, generation, "remove-test-key", lambda: self.observer.test_key_removed())
        self._step(lease_id, generation, "reload-backend", lambda: self.observer.backend_reloaded())
        if not self.observer.production_auth_ok() or not self.observer.wrong_key_denied():
            raise ValueError("production backend authentication postcheck failed; consumers remain stopped")
        self._step(lease_id, generation, "start-aster", lambda: self.observer.aster_healthy())
        self._step(lease_id, generation, "start-speech", lambda: self.observer.speech_healthy())
        if not self.observer.consumers_healthy():
            raise ValueError("consumer restoration postcheck failed; lease retained")
        state.unlink()
        lock.rmdir()
        return {"state": "ready", "mode": APPLICATION_MODE, "lease_id": lease_id, "generation": generation, "overdue": overdue}

    def _journal_status(self, lease_id: str, generation: int, event: str) -> None:
        journal = self.state_dir / "application-b60-watchdog.jsonl"
        journal.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": event, "lease_id": lease_id, "generation": generation}, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def _step(self, lease_id: str, generation: int, kind: str, check: Callable[[], bool]) -> None:
        events = []
        journal = self.state_dir / "application-b60-watchdog.jsonl"
        if journal.exists():
            events = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines() if line.strip()]
        matching = [event for event in events if event.get("lease_id") == lease_id and event.get("generation") == generation and event.get("step") == kind]
        if any(event.get("event") == "step-intent" for event in matching) and not any(event.get("event") == "step-observed" for event in matching):
            raise ValueError(f"uncertain prior application recovery step: {kind}")
        if any(event.get("event") == "step-observed" for event in matching):
            if not check():
                raise ValueError(f"application recovery postcheck failed: {kind}")
            return
        journal.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": "step-intent", "lease_id": lease_id, "generation": generation, "step": kind}, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.runner(fixed_command(kind))
        if not check():
            raise ValueError(f"application recovery postcheck failed: {kind}")
        with journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": "step-observed", "lease_id": lease_id, "generation": generation, "step": kind}, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
