"""Fixed Linux observer/deadline adapter for the cooperative lab candidate."""

from __future__ import annotations

import time
from typing import Callable, Sequence

from cooperative_lab_session import ALLOWED_CONSUMERS, LabSessionError, _canonical_commands

Probe = Callable[[Sequence[str], float], tuple[int, str]]


class CooperativeHostObserver:
    """Read-only exact observer; no arbitrary command or client is accepted."""

    def __init__(self, runner: Probe, *, allowed_backend_client: str | None = None,
                 monotonic: Callable[[], float] = time.monotonic):
        self.runner = runner
        self.allowed_backend_client = allowed_backend_client
        self.monotonic = monotonic

    def _run(self, argv: Sequence[str]) -> str:
        code, output = self.runner(argv, 5.0)
        if code != 0:
            raise LabSessionError("fixed Linux observer probe failed")
        return output.strip()

    def _state(self, vmid: str, unit: str, property_name: str) -> str:
        return self._run(("pct", "exec", vmid, "--", "systemctl", "show", unit,
                          f"--property={property_name}", "--value"))

    def __call__(self, phase: str, command: Sequence[str]) -> bool:
        stop, restore = _canonical_commands()
        if phase == "mask" and tuple(command) not in stop:
            raise LabSessionError("observer command is outside canonical mask inventory")
        if phase in {"unmask", "start"} and tuple(command) not in restore:
            raise LabSessionError("observer command is outside canonical restore inventory")
        vmid, unit = command[2], command[-1]
        if phase == "mask":
            return (self._state(vmid, unit, "UnitFileState") == "masked"
                    and self._state(vmid, unit, "ActiveState") == "inactive")
        if phase == "unmask":
            return self._state(vmid, unit, "UnitFileState") in {"enabled", "disabled"}
        return self._state(vmid, unit, "ActiveState") == "active"

    def backend_client_exclusive(self) -> bool:
        """Prove the listener has no unknown established clients; no client means NO-GO."""
        if not self.allowed_backend_client:
            return False
        output = self._run(("pct", "exec", "110", "--", "ss", "-Htn", "sport", "=", ":11435"))
        peers = []
        for line in output.splitlines():
            fields = line.split()
            if len(fields) >= 5:
                peers.append(fields[4].rsplit(":", 1)[0].strip("[]"))
        return bool(peers) and all(peer == self.allowed_backend_client for peer in peers)

    def trusted_now(self) -> float:
        return self.monotonic()
