"""Exact read-only production-restoration verifier for Stream A evaluation."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Callable

from evaluation_lease import BACKEND_TARGET, PRODUCTION_BASELINE_STATES
from stream_a_evaluation_live_plan import LivePlan


class RestorationVerificationError(RuntimeError):
    pass


MAX_OBSERVATION_BYTES = 16 * 1024
RESTORE_OBSERVER = "/usr/local/sbin/stream-a-evaluation-restore-observe"
WHOLE_HOST_LEASE = "/usr/local/sbin/local-ai-lease"


def _run(runner: Callable[..., subprocess.CompletedProcess], command: tuple[str, ...],
         *, timeout: int = 30, allowed: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess:
    result = runner(command, check=False, capture_output=True, text=True,
                    timeout=timeout)
    if result.returncode not in allowed or result.stderr:
        raise RestorationVerificationError("restoration observation command failed")
    return result


def _unique_json(raw: str) -> dict[str, object]:
    try:
        encoded = raw.encode("utf-8")
    except UnicodeError as error:
        raise RestorationVerificationError("restore observation is not UTF-8") from error
    if not 0 < len(encoded) <= MAX_OBSERVATION_BYTES:
        raise RestorationVerificationError("restore observation size is invalid")
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise RestorationVerificationError("restore observation repeats a key")
            value[key] = item
        return value
    try:
        value = json.loads(raw, object_pairs_hook=pairs)
    except json.JSONDecodeError as error:
        raise RestorationVerificationError("restore observation is invalid JSON") from error
    if not isinstance(value, dict):
        raise RestorationVerificationError("restore observation is not an object")
    return value


class RestoredProductionVerifier:
    def __init__(
        self,
        *,
        runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
        runtime_root: Path = Path("/var/lib/local-ai-lab/stream-a-evaluation"),
        clock: Callable[[], int] = lambda: int(time.time()),
    ):
        self.runner = runner
        self.runtime_root = runtime_root
        self.clock = clock

    def _guest_unit(self, target: str) -> tuple[str, str]:
        guest, unit = target.split(":", 1)
        vmid = guest.removeprefix("lxc")
        enabled = _run(self.runner, ("pct", "exec", vmid, "--", "systemctl",
                                     "is-enabled", unit), allowed=(0, 1)).stdout.strip()
        active = _run(self.runner, ("pct", "exec", vmid, "--", "systemctl",
                                    "is-active", unit), allowed=(0, 3)).stdout.strip()
        return enabled, active

    def __call__(self, plan: LivePlan) -> bool:
        try:
            result = _run(self.runner, (
                RESTORE_OBSERVER, "--lease-id", plan.lease_id,
                "--generation", "1", "--observe-authorized",
            ))
            observation = _unique_json(result.stdout)
            if (set(observation) != {
                    "lease_id", "generation", "observed_at", "backend_active",
                    "endpoint_authenticated", "endpoint_idle", "gpu_holders"}
                    or observation["lease_id"] != plan.lease_id
                    or observation["generation"] != 1
                    or type(observation["observed_at"]) is not int
                    or abs(self.clock() - observation["observed_at"]) > 15
                    or observation["backend_active"] is not True
                    or observation["endpoint_authenticated"] is not True
                    or observation["endpoint_idle"] is not True
                    or observation["gpu_holders"] != [BACKEND_TARGET]):
                return False
            for target, expected in PRODUCTION_BASELINE_STATES:
                if expected != "enabled+active" \
                        or self._guest_unit(target) != ("enabled", "active"):
                    return False
            if self._guest_unit(BACKEND_TARGET) != ("enabled", "active"):
                return False
            lease = _unique_json(_run(
                self.runner, (WHOLE_HOST_LEASE, "status"), timeout=15).stdout)
            if lease != {"state": "ready"}:
                return False
            for name in ("lease.json", "lease.lock", "lease.operation.lock"):
                if (self.runtime_root / name).exists():
                    return False
            return True
        except (OSError, ValueError, RestorationVerificationError):
            return False
