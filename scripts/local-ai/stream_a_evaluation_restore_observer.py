"""Read-only live restore observation for the Stream A watchdog."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


EXPECTED_EXECUTABLE = "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"
EXPECTED_CGROUP = "/lxc/110/ns/system.slice/aster-llama.service"
F2_RECURRING_TIMERS = (
    "f2-preflight-prepare.timer", "f2-preflight-final.timer",
)
M3_PROCESS_PATTERN = r"^/usr/bin/python3 nlu_calibration_runner.py "


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
            # A process that has fully exited cannot retain the render node.
            # Ignore only that narrow race and continue the complete scan.  If
            # the proc entry still exists (including rapid PID reuse or a
            # malformed/partially readable live entry), fail closed.
            if not proc.exists():
                continue
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
    match = re.fullmatch(
        r"stream-a-evaluation-(20[0-9]{2}-[01][0-9]-[0-3][0-9])-[0-9a-f]{16}",
        lease_id,
    )
    if match is None:
        raise RuntimeError("evaluation lease identity is invalid")
    compact_cycle = match.group(1).replace("-", "")
    f2_timers = {}
    for unit in (*F2_RECURRING_TIMERS,
                 f"f2-preflight-prepare-{compact_cycle}.timer",
                 f"f2-preflight-final-{compact_cycle}.timer"):
        enabled_code, enabled = run(("systemctl", "is-enabled", unit))
        active_code, active = run(("systemctl", "is-active", unit))
        expected_enabled = "disabled" if unit in F2_RECURRING_TIMERS else "not-found"
        if (enabled_code != 1 or enabled != expected_enabled
                or active_code != 3 or active != "inactive"):
            raise RuntimeError("F2 schedule did not restore exactly")
        f2_timers[unit] = [enabled, active]
    d4_code, d4_state = run((
        "pct", "exec", "104", "--", "systemctl", "is-active",
        "aster-d4-candidate-h.service",
    ))
    m3_code, m3_process = run((
        "pct", "exec", "110", "--", "pgrep", "-f", M3_PROCESS_PATTERN,
    ))
    if d4_code != 3 or d4_state != "inactive" or m3_code != 1 or m3_process:
        raise RuntimeError("evaluation child remains after restoration")
    return {
        "lease_id": lease_id,
        "generation": generation,
        "observed_at": int(time.time()),
        "backend_active": True,
        "endpoint_authenticated": True,
        "endpoint_idle": True,
        "gpu_holders": ["lxc110:aster-llama.service"],
        "f2_timers": f2_timers,
        "evaluation_children": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lease-id")
    parser.add_argument("--generation", type=int)
    parser.add_argument("--observe-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.observe_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
        return 0
    if not args.lease_id or args.generation is None or args.generation < 1:
        return 1
    print(json.dumps(collect_restore_observation(
        lease_id=args.lease_id, generation=args.generation),
        sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
