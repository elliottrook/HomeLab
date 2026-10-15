"""Narrow effect runner for the Local AI lease candidate.

This module is deliberately separate from the watchdog decision logic. It can
only execute the exact ``pct exec ... systemctl {start,stop}`` commands emitted
by the candidate controller, with a bounded timeout and no shell.
"""

from __future__ import annotations

import subprocess
from typing import Sequence

ALLOWLIST = (
    ("104", "aster-agent.service"),
    ("110", "aster-llama.service"),
    ("116", "aster-speech.service"),
)


def command_for(vmid: str, unit: str, action: str) -> tuple[str, ...]:
    if (vmid, unit) not in ALLOWLIST or action not in {"start", "stop"}:
        raise ValueError("effect is outside the fixed lease allowlist")
    return ("pct", "exec", vmid, "--", "systemctl", action, unit)


class EffectError(RuntimeError):
    """An allowlisted effect could not be completed or verified."""


class EffectRunner:
    def __init__(self, *, timeout: float = 15.0):
        if timeout <= 0:
            raise ValueError("effect timeout must be positive")
        self.timeout = timeout

    def run(self, argv: Sequence[str]) -> None:
        command = tuple(argv)
        if len(command) != 7 or command[:2] != ("pct", "exec"):
            raise EffectError("effect is outside the fixed lease boundary")
        vmid, unit, action = command[2], command[6], command[5]
        if (vmid, unit) not in ALLOWLIST:
            raise EffectError("effect is outside the fixed lease allowlist")
        if command != command_for(vmid, unit, action):
            raise EffectError("effect is outside the fixed lease allowlist")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise EffectError("allowlisted effect did not complete") from exc
        if result.returncode != 0:
            raise EffectError("allowlisted effect returned failure")
