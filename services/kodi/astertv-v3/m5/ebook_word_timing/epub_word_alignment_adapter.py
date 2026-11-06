"""Fixed host adapter for the Aster Speech word-alignment benchmark."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from typing import Callable

from epub_word_alignment_transaction import (DEADLINE_SECONDS, RESULT_MAX_BYTES,
                                               TransactionError, validate_result)


WORKLOAD_ID = "astertv-v3-ebook-word-alignment-v1"
GUEST_SCRIPT = "/opt/epub-narration/tools/ebook_word_alignment_benchmark.py"
GUEST_SCRIPT_SHA256 = "04fb4971b13cf803957c1cce501035be2583607ab7727e095d2fbf8130d5b04e"
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")


class AdapterError(RuntimeError):
    pass


def unit_name(lease_id: str, generation: int) -> str:
    if not LEASE_RE.fullmatch(lease_id) or type(generation) is not int or generation < 1:
        raise AdapterError("EBOOK_ALIGNMENT_LEASE_IDENTITY")
    digest = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:16]
    return f"aster-ebook-align-{digest}.service"


def guest_command(lease_id: str, generation: int) -> tuple[str, ...]:
    unit = unit_name(lease_id, generation)
    return (
        "pct", "exec", "116", "--", "systemd-run", "--quiet", "--collect", "--wait", "--pipe",
        f"--unit={unit}", "--property=Type=exec", "--property=User=root",
        "--property=Restart=no", "--property=Nice=10", "--property=IOSchedulingClass=idle",
        f"--property=RuntimeMaxSec={DEADLINE_SECONDS}",
        "/opt/whisper-bench/bin/python", GUEST_SCRIPT,
        "--lease-id", lease_id, "--generation", str(generation),
    )


def stop_command(lease_id: str, generation: int) -> tuple[str, ...]:
    return ("pct", "exec", "116", "--", "systemctl", "stop", unit_name(lease_id, generation))


def absent(runner: Callable[[tuple[str, ...], float], tuple[int, str]], *,
           lease_id: str, generation: int) -> bool:
    unit = unit_name(lease_id, generation)
    active, _ = runner(("pct", "exec", "116", "--", "systemctl", "is-active", unit), 15.0)
    process, output = runner(("pct", "exec", "116", "--", "pgrep", "-af",
                              "ebook_word_alignment_benchmark.py"), 15.0)
    return active != 0 and process == 1 and not output.strip()


def run(*, lease_id: str, generation: int, deadline_epoch: int,
        heartbeat: Callable[[], None],
        process_factory: Callable[..., object] = subprocess.Popen,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        runner: Callable[[tuple[str, ...], float], tuple[int, str]] | None = None) -> dict[str, object]:
    current = int(clock())
    if (type(deadline_epoch) is not int or deadline_epoch <= current
            or deadline_epoch > current + DEADLINE_SECONDS):
        raise AdapterError("EBOOK_ALIGNMENT_DEADLINE")
    runner = runner or (lambda command, timeout: (
        lambda result: (result.returncode, result.stdout))(
            subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)))
    if not absent(runner, lease_id=lease_id, generation=generation):
        raise AdapterError("EBOOK_ALIGNMENT_TARGET_BUSY")
    pin_code, pin_output = runner(
        ("pct", "exec", "116", "--", "sha256sum", GUEST_SCRIPT), 15.0)
    if pin_code != 0 or pin_output.strip() != f"{GUEST_SCRIPT_SHA256}  {GUEST_SCRIPT}":
        raise AdapterError("EBOOK_ALIGNMENT_GUEST_PIN")
    process = None
    capture = Path(tempfile.mkdtemp(prefix="ebook-align-", dir="/run/local-ai-lab"))
    capture.chmod(0o700)
    stdout_path = capture / "stdout.json"
    stderr_path = capture / "stderr.json"
    stdout = stdout_path.open("xb")
    stderr = stderr_path.open("xb")
    stdout_path.chmod(0o600)
    stderr_path.chmod(0o600)
    failure = None
    try:
        process = process_factory(guest_command(lease_id, generation), stdout=stdout, stderr=stderr,
                                  start_new_session=True)
        while True:
            heartbeat()
            if clock() >= deadline_epoch:
                raise AdapterError("EBOOK_ALIGNMENT_DEADLINE_REACHED")
            if stdout_path.stat().st_size > RESULT_MAX_BYTES or stderr_path.stat().st_size > RESULT_MAX_BYTES:
                raise AdapterError("EBOOK_ALIGNMENT_OUTPUT_SIZE")
            status = process.poll()
            if status is not None:
                stdout.flush(); stderr.flush(); stdout.close(); stderr.close()
                stdout = stderr = None
                raw_out = stdout_path.read_bytes()
                raw_err = stderr_path.read_bytes()
                if status != 0:
                    try:
                        detail = json.loads(raw_err).get("code")
                    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                        detail = None
                    if not isinstance(detail, str) or not re.fullmatch(r"[A-Z0-9_-]{1,80}", detail):
                        detail = "UNCLASSIFIED"
                    raise AdapterError("EBOOK_ALIGNMENT_GUEST_" + detail)
                try:
                    result = json.loads(raw_out)
                    validate_result(result)
                except (UnicodeDecodeError, json.JSONDecodeError, TransactionError) as error:
                    raise AdapterError("EBOOK_ALIGNMENT_RESULT_INVALID") from error
                return result
            sleep(min(1.0, max(0.0, deadline_epoch - clock())))
    except BaseException as error:
        failure = error
        raise
    finally:
        for stream in (stdout, stderr):
            if stream is not None:
                stream.close()
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except OSError:
                process.terminate()
            try:
                process.wait(timeout=10)
            except Exception:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except OSError:
                    process.kill()
                process.wait()
        runner(stop_command(lease_id, generation), 30.0)
        for path in (stdout_path, stderr_path):
            if path.exists():
                path.unlink()
        capture.rmdir()
        if failure is None and not absent(runner, lease_id=lease_id, generation=generation):
            raise AdapterError("EBOOK_ALIGNMENT_CLEANUP")


if __name__ == "__main__":
    raise SystemExit("registered adapter module; not a direct entrypoint")
