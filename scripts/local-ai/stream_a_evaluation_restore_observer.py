"""Read-only live restore observation for the Stream A watchdog."""

from __future__ import annotations

import json
import subprocess
import time
from typing import Callable, Sequence


def collect_restore_observation(
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess] = subprocess.run,
) -> dict[str, object]:
    def run(command: tuple[str, ...]) -> str:
        result = runner(command, check=False, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise RuntimeError("fixed restore observation command failed")
        return result.stdout.strip()

    backend = run(("pct", "exec", "110", "--", "systemctl", "is-active", "aster-llama.service"))
    authenticated = run(("pct", "exec", "110", "--", "/usr/local/sbin/aster-llama-production-auth-probe"))
    idle = run(("pct", "exec", "110", "--", "/usr/local/sbin/aster-llama-production-idle-probe"))
    holders = run(("pct", "exec", "110", "--", "/usr/local/sbin/aster-llama-gpu-holder-probe"))
    if backend != "active" or authenticated != "ok" or idle != "idle":
        raise RuntimeError("accepted backend is not healthy and idle")
    gpu_holders = [item for item in holders.splitlines() if item]
    if gpu_holders != ["lxc110:aster-llama.service"]:
        raise RuntimeError("GPU holder is not the accepted backend")
    return {
        "observed_at": int(time.time()),
        "backend_active": True,
        "endpoint_authenticated": True,
        "endpoint_idle": True,
        "gpu_holders": gpu_holders,
    }


def main() -> int:
    print(json.dumps(collect_restore_observation(), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
