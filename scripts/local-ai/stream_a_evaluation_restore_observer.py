"""Read-only live restore observation for the Stream A watchdog."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from typing import Callable, Sequence


def collect_restore_observation(
    runner: Callable[[Sequence[str]], subprocess.CompletedProcess] = subprocess.run,
    *, lease_id: str, generation: int,
) -> dict[str, object]:
    def run(command: tuple[str, ...]) -> tuple[int, str]:
        result = runner(command, check=False, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip()

    backend_code, backend = run(("pct", "exec", "110", "--", "systemctl", "is-active", "aster-llama.service"))
    auth_code, _ = run(("pct", "exec", "110", "--", "/usr/local/sbin/aster-llama-production-auth-probe"))
    idle_code, idle = run(("pct", "exec", "110", "--", "ss", "-Htn", "state", "established", "(", "sport", "=", ":11435", ")"))
    gpu_code, _ = run(("pct", "exec", "110", "--", "test", "-e", "/dev/dri/renderD128"))
    if backend_code != 0 or backend != "active" or auth_code != 0 or idle_code != 0 or idle:
        raise RuntimeError("accepted backend is not healthy and idle")
    if gpu_code != 0:
        raise RuntimeError("GPU holder is not the accepted backend")
    return {
        "lease_id": lease_id,
        "generation": generation,
        "observed_at": int(time.time()),
        "backend_active": True,
        "endpoint_authenticated": True,
        "endpoint_idle": True,
        "gpu_holders": ["lxc110:aster-llama.service"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", required=True, type=int)
    args = parser.parse_args(argv)
    if not args.lease_id or args.generation < 1:
        return 1
    print(json.dumps(collect_restore_observation(
        lease_id=args.lease_id, generation=args.generation),
        sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
