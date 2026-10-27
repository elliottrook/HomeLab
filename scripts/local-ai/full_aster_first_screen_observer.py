"""Fixed live observer for full-Aster first-screen recovery."""
from __future__ import annotations

import subprocess
from typing import Callable, Sequence

from full_aster_first_screen_candidate import UNIT
from full_aster_first_screen_recovery import MOUNT_VALUE


MODEL_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
BINARY_SHA256 = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
UNIT_SHA256 = "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3"


class ObservationError(RuntimeError):
    pass


def _default_runner(command: Sequence[str], timeout: float):
    value = subprocess.run(tuple(command), capture_output=True, text=True,
                           timeout=timeout, check=False)
    return value.returncode, value.stdout.strip()


class FixedObserver:
    def __init__(self, runner: Callable[[Sequence[str], float], tuple[int, str]] = _default_runner):
        self.runner = runner

    def _run(self, command, timeout=15.0, allowed=(0,)) -> tuple[int, str]:
        code, output = self.runner(tuple(command), timeout)
        if code not in allowed:
            raise ObservationError("fixed observation command failed")
        return code, output.strip()

    def candidate_absent(self) -> bool:
        code, state = self._run(("pct", "exec", "110", "--", "systemctl",
                                 "is-active", UNIT), allowed=(0, 3, 4))
        pcode, pids = self._run(("pct", "exec", "110", "--", "pgrep", "-f",
            "^/opt/aster-sycl-b11429/.*/llama-server .*Qwen3.6-35B-A3B-Q4_K_M.gguf"),
            allowed=(0, 1))
        return code != 0 and state in {"inactive", "failed", "unknown"} \
            and pcode == 1 and not pids

    def mount_state(self) -> str:
        _code, config = self._run(("pct", "config", "110"))
        rows = [line.split(": ", 1)[1] for line in config.splitlines()
                if line.startswith("mp0: ")]
        if not rows:
            return "absent"
        return "exact" if rows == [MOUNT_VALUE] else "foreign"

    def guest_running(self) -> bool:
        _code, status = self._run(("pct", "status", "110"))
        return status == "status: running"

    def _hash(self, path: str, expected: str) -> bool:
        code, output = self.runner(("pct", "exec", "110", "--", "sha256sum", path), 60.0)
        return code == 0 and output.split()[:1] == [expected]

    def exact_baseline_restored(self) -> bool:
        if not self.guest_running() or self.mount_state() != "absent" \
                or not self.candidate_absent():
            return False
        code, active = self.runner(("pct", "exec", "110", "--", "systemctl",
                                    "is-active", "aster-llama.service"), 15.0)
        if code != 0 or active.strip() != "active":
            return False
        checks = (
            ("/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf", MODEL_SHA256),
            ("/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server", BINARY_SHA256),
            ("/etc/systemd/system/aster-llama.service", UNIT_SHA256),
        )
        if not all(self._hash(path, digest) for path, digest in checks):
            return False
        code, _ = self.runner(("pct", "exec", "110", "--",
                               "/usr/local/sbin/aster-llama-production-auth-probe"), 30.0)
        return code == 0
