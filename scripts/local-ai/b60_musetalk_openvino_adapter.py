"""Fixed host adapter for the booked OpenVINO MuseTalk render."""

from __future__ import annotations

import json
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

import b60_musetalk_xpu_adapter as base
from b60_musetalk_openvino_transaction import (
    DEADLINE_SECONDS, RESULT_MAX_BYTES, TransactionError, WORKLOAD_ID, validate_result,
)


GUEST_SCRIPT = "/opt/aster-news-video-xpu/b60_musetalk_openvino_guest.py"
GUEST_SCRIPT_SHA256 = "9ebfacfcb006b8f2729fac19c161b587ed55d77eff73b9152d5c515c240a39aa"
COMMON_GUEST_SCRIPT = "/opt/aster-news-video-xpu/b60_musetalk_xpu_guest.py"
COMMON_GUEST_SCRIPT_SHA256 = "224c7b45aab24076c15b5009efd77f679f0b271767d8bddbff64ab6309390209"
PYTHONPATH = "/opt/aster-news-video-xpu/venv/lib/python3.12/site-packages:/opt/aster-news-video-xpu"
XPU_RUNTIME_LIB = "/opt/aster-news-video-xpu/runtime/root/usr/lib/x86_64-linux-gnu"
XPU_RUNTIME_LOCAL_LIB = "/opt/aster-news-video-xpu/runtime/root/usr/local/lib"
LD_LIBRARY_PATH = f"{XPU_RUNTIME_LIB}:{XPU_RUNTIME_LOCAL_LIB}:/opt/aster-news-video-xpu/venv/lib:/opt/aster-news-video-xpu/ov-venv/lib/python3.12/site-packages/openvino/libs"
OCL_ICD_FILENAMES = f"{XPU_RUNTIME_LIB}/intel-opencl/libigdrcl.so"
AdapterError = base.AdapterError


def absent(runner, *, lease_id: str, generation: int) -> bool:
    active, _ = runner(("pct", "exec", "110", "--", "systemctl", "is-active",
                        base.unit_name(lease_id, generation)), 15.0)
    process, output = runner(("pct", "exec", "110", "--", "pgrep", "-af",
                              "b60_musetalk_openvino_guest.py"), 15.0)
    return active != 0 and process == 1 and not output.strip()


def guest_command(lease_id: str, generation: int) -> tuple[str, ...]:
    return (
        "pct", "exec", "110", "--", "systemd-run", "--quiet", "--collect", "--wait", "--pipe",
        f"--unit={base.unit_name(lease_id, generation)}", "--property=Type=exec",
        "--property=User=root", "--property=Restart=no", "--property=Nice=10",
        "--property=IOSchedulingClass=idle", "--property=PrivateNetwork=yes",
        "--property=MemoryMax=12G", "--property=MemorySwapMax=0",
        f"--property=RuntimeMaxSec={DEADLINE_SECONDS}", "/usr/bin/env",
        f"PYTHONPATH={PYTHONPATH}", "MUSETALK_DEVICE=cpu", "HF_HUB_OFFLINE=1",
        f"LD_LIBRARY_PATH={LD_LIBRARY_PATH}",
        f"OCL_ICD_FILENAMES={OCL_ICD_FILENAMES}",
        "TRANSFORMERS_OFFLINE=1", "TOKENIZERS_PARALLELISM=false",
        "OPENVINO_TELEMETRY_STATISTICS=0", "/opt/aster-news-video-xpu/ov-venv/bin/python",
        GUEST_SCRIPT, "--workload-id", WORKLOAD_ID, "--lease-id", lease_id,
        "--generation", str(generation),
    )


def run(*, lease_id: str, generation: int, deadline_epoch: int, heartbeat,
        process_factory=subprocess.Popen, clock=time.time, sleep=time.sleep, runner=None):
    current = int(clock())
    if (type(deadline_epoch) is not int or deadline_epoch <= current
            or deadline_epoch > current + DEADLINE_SECONDS):
        raise AdapterError("MUSETALK_OV_DEADLINE")
    runner = runner or (lambda command, timeout: (lambda result: (result.returncode, result.stdout))(
        subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)))
    if not absent(runner, lease_id=lease_id, generation=generation):
        raise AdapterError("MUSETALK_OV_TARGET_BUSY")
    code, output = runner(("pct", "exec", "110", "--", "sha256sum", GUEST_SCRIPT), 15.0)
    if code != 0 or output.strip() != f"{GUEST_SCRIPT_SHA256}  {GUEST_SCRIPT}":
        raise AdapterError("MUSETALK_OV_GUEST_PIN")
    code, output = runner(("pct", "exec", "110", "--", "sha256sum", COMMON_GUEST_SCRIPT), 15.0)
    if code != 0 or output.strip() != f"{COMMON_GUEST_SCRIPT_SHA256}  {COMMON_GUEST_SCRIPT}":
        raise AdapterError("MUSETALK_OV_COMMON_GUEST_PIN")
    start_epoch = int(clock()); process = None; failure = None
    capture = Path(tempfile.mkdtemp(prefix="musetalk-ov-", dir="/run/local-ai-lab")); capture.chmod(0o700)
    stdout_path = capture / "stdout.json"; stderr_path = capture / "stderr.log"
    stdout = stdout_path.open("xb"); stderr = stderr_path.open("xb")
    try:
        process = process_factory(guest_command(lease_id, generation), stdout=stdout, stderr=stderr,
                                  start_new_session=True)
        while True:
            heartbeat()
            if clock() >= deadline_epoch: raise AdapterError("MUSETALK_OV_DEADLINE_REACHED")
            if stdout_path.stat().st_size > RESULT_MAX_BYTES or stderr_path.stat().st_size > 4*1024*1024:
                raise AdapterError("MUSETALK_OV_OUTPUT_SIZE")
            status = process.poll()
            if status is not None:
                stdout.flush(); stderr.flush(); stdout.close(); stderr.close(); stdout = stderr = None
                raw_out = stdout_path.read_bytes(); raw_err = stderr_path.read_bytes()
                if status != 0:
                    raise AdapterError("MUSETALK_OV_GUEST_" + base.guest_failure_detail(raw_err))
                try:
                    result = json.loads(raw_out); validate_result(result)
                except (UnicodeDecodeError, json.JSONDecodeError, TransactionError) as error:
                    raise AdapterError("MUSETALK_OV_RESULT_INVALID") from error
                faults, fault_output = runner(("journalctl", "-k", "--since", f"@{start_epoch}",
                                                "--no-pager", "-o", "cat"), 30.0)
                if faults != 0 or re.search(r"\bxe\b.*\b(fault|reset|error)\b", fault_output, re.I):
                    raise AdapterError("MUSETALK_OV_XE_FAULT")
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
                base.unit_name(lease_id, generation)), 30.0)
        for path in (stdout_path, stderr_path):
            if path.exists(): path.unlink()
        capture.rmdir()
        if failure is None and not absent(runner, lease_id=lease_id, generation=generation):
            raise AdapterError("MUSETALK_OV_CLEANUP")
