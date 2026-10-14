"""Fail-closed recovery candidate for application-only B60 effects.

The whole-host watchdog cannot recover an application lease because that lease
owns a sidecar, a temporary LXC110 ingress policy and a temporary backend key.
This candidate deliberately restores those effects before restarting consumers.
It is offline-only until the fixed host helper commands and observer are
installed and independently validated.
"""

from __future__ import annotations

import json
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

    def recover(self, *, lease_id: str, generation: int) -> dict[str, object]:
        if not self.allow_effects:
            raise ValueError("application watchdog is advisory-only; live effects are disabled")
        state = self.state_dir / STATE_NAME
        lock = self.state_dir / LOCK_NAME
        if not state.exists() or not lock.exists():
            raise ValueError("application lease state and lock are required")
        record = json.loads(state.read_text(encoding="utf-8"))
        if (record.get("mode"), record.get("lease_id"), record.get("generation")) != (APPLICATION_MODE, lease_id, generation):
            raise ValueError("application lease identity does not match")

        self._step("stop-sidecar", lambda: self.observer.sidecar_stopped())
        self._step("restore-ingress", lambda: self.observer.ingress_restored())
        self._step("remove-test-key", lambda: self.observer.test_key_removed())
        self._step("reload-backend", lambda: self.observer.backend_reloaded())
        if not self.observer.production_auth_ok() or not self.observer.wrong_key_denied():
            raise ValueError("production backend authentication postcheck failed; consumers remain stopped")
        self._step("start-aster", lambda: self.observer.aster_healthy())
        self._step("start-speech", lambda: self.observer.speech_healthy())
        if not self.observer.consumers_healthy():
            raise ValueError("consumer restoration postcheck failed; lease retained")
        state.unlink()
        lock.rmdir()
        return {"state": "ready", "mode": APPLICATION_MODE, "lease_id": lease_id, "generation": generation}

    def _step(self, kind: str, check: Callable[[], bool]) -> None:
        self.runner(fixed_command(kind))
        if not check():
            raise ValueError(f"application recovery postcheck failed: {kind}")
