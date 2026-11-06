"""Fixed host adapter for the booked Aster MuseTalk XPU render."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from typing import Callable

from b60_musetalk_xpu_transaction import (
    DEADLINE_SECONDS, RESULT_MAX_BYTES, TransactionError, WORKLOAD_ID, validate_result,
)


GUEST_SCRIPT = "/opt/aster-news-video-xpu/b60_musetalk_xpu_guest.py"
GUEST_SCRIPT_SHA256 = "224c7b45aab24076c15b5009efd77f679f0b271767d8bddbff64ab6309390209"
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")
LIBRARY_PATH = (
    "/opt/aster-news-video-xpu/runtime/root/usr/lib/x86_64-linux-gnu:"
    "/opt/aster-news-video-xpu/runtime/root/usr/local/lib:"
    "/opt/aster-news-video-xpu/venv/lib/python3.12/site-packages/torch/lib"
)


class AdapterError(RuntimeError):
    pass


def guest_failure_detail(raw: bytes) -> str:
    stage_name = None
    for line in reversed(raw.splitlines()):
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        code = value.get("code") if isinstance(value, dict) else None
        if isinstance(code, str) and re.fullmatch(r"[A-Za-z0-9_:-]{1,120}", code):
            return code
        stage_value = value.get("stage") if isinstance(value, dict) else None
        if (stage_name is None and isinstance(stage_value, str)
                and re.fullmatch(r"[A-Z0-9_]{1,80}", stage_value)):
            stage_name = stage_value
    return f"NATIVE_CRASH_AFTER_{stage_name}" if stage_name else "UNCLASSIFIED"


def unit_name(lease_id: str, generation: int) -> str:
    if not LEASE_RE.fullmatch(lease_id) or type(generation) is not int or generation < 1:
        raise AdapterError("MUSETALK_IDENTITY")
    digest = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:16]
    return f"aster-musetalk-xpu-{digest}.service"


def guest_command(lease_id: str, generation: int) -> tuple[str, ...]:
    return (
        "pct", "exec", "110", "--", "systemd-run", "--quiet", "--collect", "--wait", "--pipe",
        f"--unit={unit_name(lease_id, generation)}", "--property=Type=exec", "--property=User=root",
        "--property=Restart=no", "--property=Nice=10", "--property=IOSchedulingClass=idle",
        "--property=PrivateNetwork=yes", "--property=MemoryMax=12G",
        "--property=MemorySwapMax=0",
        f"--property=RuntimeMaxSec={DEADLINE_SECONDS}", "/usr/bin/env",
        f"LD_LIBRARY_PATH={LIBRARY_PATH}", "MUSETALK_DEVICE=xpu:0", "HF_HUB_OFFLINE=1",
        "TRANSFORMERS_OFFLINE=1", "TOKENIZERS_PARALLELISM=false",
        "/opt/aster-news-video-xpu/venv/bin/python", GUEST_SCRIPT,
        "--workload-id", WORKLOAD_ID, "--lease-id", lease_id, "--generation", str(generation),
    )


def absent(runner: Callable[[tuple[str, ...], float], tuple[int, str]], *,
           lease_id: str, generation: int) -> bool:
    active, _ = runner(("pct", "exec", "110", "--", "systemctl", "is-active",
                        unit_name(lease_id, generation)), 15.0)
    process, output = runner(("pct", "exec", "110", "--", "pgrep", "-af",
                              "b60_musetalk_xpu_guest.py"), 15.0)
    return active != 0 and process == 1 and not output.strip()


def run(*, lease_id: str, generation: int, deadline_epoch: int,
        heartbeat: Callable[[], None], process_factory: Callable[..., object] = subprocess.Popen,
        clock: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep,
        runner: Callable[[tuple[str, ...], float], tuple[int, str]] | None = None) -> dict[str, object]:
    current = int(clock())
    if (type(deadline_epoch) is not int or deadline_epoch <= current
            or deadline_epoch > current + DEADLINE_SECONDS):
        raise AdapterError("MUSETALK_DEADLINE")
    runner = runner or (lambda command, timeout: (lambda result: (result.returncode, result.stdout))(
        subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)))
    if not absent(runner, lease_id=lease_id, generation=generation):
        raise AdapterError("MUSETALK_TARGET_BUSY")
    code, output = runner(("pct", "exec", "110", "--", "sha256sum", GUEST_SCRIPT), 15.0)
    if code != 0 or output.strip() != f"{GUEST_SCRIPT_SHA256}  {GUEST_SCRIPT}":
        raise AdapterError("MUSETALK_GUEST_PIN")

    start_epoch = int(clock())
    process = None; failure = None
    capture = Path(tempfile.mkdtemp(prefix="musetalk-xpu-", dir="/run/local-ai-lab")); capture.chmod(0o700)
    stdout_path = capture / "stdout.json"; stderr_path = capture / "stderr.log"
    stdout = stdout_path.open("xb"); stderr = stderr_path.open("xb")
    stdout_path.chmod(0o600); stderr_path.chmod(0o600)
    try:
        process = process_factory(guest_command(lease_id, generation), stdout=stdout, stderr=stderr,
                                  start_new_session=True)
        while True:
            heartbeat()
            if clock() >= deadline_epoch:
                raise AdapterError("MUSETALK_DEADLINE_REACHED")
            if stdout_path.stat().st_size > RESULT_MAX_BYTES or stderr_path.stat().st_size > 4 * 1024 * 1024:
                raise AdapterError("MUSETALK_OUTPUT_SIZE")
            status = process.poll()
            if status is not None:
                stdout.flush(); stderr.flush(); stdout.close(); stderr.close(); stdout = stderr = None
                raw_out = stdout_path.read_bytes(); raw_err = stderr_path.read_bytes()
                if status != 0:
                    raise AdapterError("MUSETALK_GUEST_" + guest_failure_detail(raw_err))
                try:
                    result = json.loads(raw_out); validate_result(result)
                except (UnicodeDecodeError, json.JSONDecodeError, TransactionError) as error:
                    raise AdapterError("MUSETALK_RESULT_INVALID") from error
                faults, fault_output = runner(("journalctl", "-k", "--since", f"@{start_epoch}",
                                                "--no-pager", "-o", "cat"), 30.0)
                if faults != 0:
                    raise AdapterError("MUSETALK_XE_CHECK_UNAVAILABLE")
                if re.search(r"\bxe\b.*\b(fault|reset|error)\b", fault_output, re.IGNORECASE):
                    raise AdapterError("MUSETALK_XE_FAULT")
                return result
            sleep(min(1.0, max(0.0, deadline_epoch - clock())))
    except BaseException as error:
        failure = error; raise
    finally:
        for stream in (stdout, stderr):
            if stream is not None: stream.close()
        if process is not None and process.poll() is None:
            try: process.send_signal(signal.SIGTERM)
            except OSError: process.terminate()
            try: process.wait(timeout=15)
            except Exception: process.kill(); process.wait()
        runner(("pct", "exec", "110", "--", "systemctl", "stop",
                unit_name(lease_id, generation)), 30.0)
        for path in (stdout_path, stderr_path):
            if path.exists(): path.unlink()
        capture.rmdir()
        if failure is None and not absent(runner, lease_id=lease_id, generation=generation):
            raise AdapterError("MUSETALK_CLEANUP")


if __name__ == "__main__":
    raise SystemExit("registered adapter module; not a direct entrypoint")
