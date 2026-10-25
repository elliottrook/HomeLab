"""Read-only live restore observation for the Stream A watchdog."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


EXPECTED_EXECUTABLE = "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"
EXPECTED_CGROUP = "/lxc/110/ns/system.slice/aster-llama.service"


@dataclass(frozen=True)
class GpuHolder:
    pid: int
    starttime_ticks: int
    cgroup: str
    executable: str


def scan_gpu_holders(proc_root: Path = Path("/proc")) -> tuple[GpuHolder, ...]:
    holders = []
    for proc in proc_root.glob("[0-9]*"):
        try:
            pid = int(proc.name)
        except ValueError:
            continue
        matched = False
        try:
            for fd in (proc / "fd").iterdir():
                try:
                    if os.readlink(fd) == "/dev/dri/renderD128":
                        matched = True
                        break
                except FileNotFoundError:
                    continue
                except PermissionError as exc:
                    raise RuntimeError("GPU fd observation was not permitted") from exc
            if not matched:
                continue
            stat_text = (proc / "stat").read_text(encoding="ascii")
            starttime = int(stat_text.rsplit(")", 1)[1].split()[19])
            cgroup = (proc / "cgroup").read_text(encoding="utf-8").strip()
            executable = os.readlink(proc / "exe")
        except FileNotFoundError as exc:
            raise RuntimeError("GPU holder PID changed during observation") from exc
        except (OSError, ValueError, UnicodeError) as exc:
            raise RuntimeError("GPU holder observation failed") from exc
        holders.append(GpuHolder(pid, starttime, cgroup, executable))
    return tuple(holders)


def require_exact_gpu_holder(holders: tuple[GpuHolder, ...]) -> None:
    if len(holders) != 1:
        raise RuntimeError("GPU holder set is not exactly one accepted holder")
    holder = holders[0]
    if holder.executable != EXPECTED_EXECUTABLE or not holder.cgroup.endswith(EXPECTED_CGROUP):
        raise RuntimeError("GPU holder identity is not the accepted llama service")


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
    holders = scan_gpu_holders()
    if backend_code != 0 or backend != "active" or auth_code != 0 or idle_code != 0 or idle:
        raise RuntimeError("accepted backend is not healthy and idle")
    require_exact_gpu_holder(holders)
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
    parser.add_argument("--observe-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.observe_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
        return 0
    if not args.lease_id or args.generation < 1:
        return 1
    print(json.dumps(collect_restore_observation(
        lease_id=args.lease_id, generation=args.generation),
        sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
