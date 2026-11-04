"""Fixed host adapter for candidate-g; source-only until separately installed."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from typing import Callable

from sa3_evidence_envelope_transaction import (
    DEADLINE_SECONDS, RESULT_MAX_BYTES, TransactionError, WORKLOAD_ID,
    validate_result,
)
from sa3_listener_adapter import (
    AdapterError, _cleanup_capture, _open_capture_file, _prepare_capture_root,
    _stop_process, _verify_capture_directory, _verify_capture_file, scope_unit,
)


LISTENER = "/usr/local/libexec/local-ai-lease/full-inference-pilot/aster_llama_sa3_evidence_envelope_wrapper.py"
PORT = 11436
CASES = 20
PER_REQUEST_TIMEOUT_SECONDS = 120
TRACEBACK_CLASS_RE = re.compile(r"([A-Za-z][A-Za-z0-9_.]{0,127})(?::.*)?")
ERROR_CLASS_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}")


def bounded_guest_failure(stderr: bytes, stdout: bytes = b"",
                          status: int | None = None) -> str:
    decoded = []
    for payload in (stderr, stdout):
        try:
            decoded.append(payload.decode("utf-8").splitlines())
        except UnicodeDecodeError:
            decoded.append([])
    for lines in decoded:
        for line in reversed(lines):
            candidates = [line.strip()]
            if "{" in line:
                candidates.append(line[line.find("{"):].strip())
            for candidate in candidates:
                try:
                    value = json.loads(candidate)
                except json.JSONDecodeError:
                    continue
                detail = value.get("code") if isinstance(value, dict) else None
                if isinstance(detail, str) and 1 <= len(detail) <= 160:
                    return detail
    for lines in decoded:
        for line in reversed(lines):
            match = TRACEBACK_CLASS_RE.fullmatch(line.strip())
            if match:
                error_class = match.group(1).rsplit(".", 1)[-1]
                if ERROR_CLASS_RE.fullmatch(error_class):
                    return "candidate-g guest traceback-class:" + error_class
    if type(status) is int and -255 <= status <= 255:
        return (f"candidate-g guest exit-status:{status};"
                f"stdout-bytes:{len(stdout)};stderr-bytes:{len(stderr)}")
    return "unclassified guest failure"


def listener_command(*, lease_id: str, generation: int) -> tuple[str, ...]:
    return ("pct", "exec", "110", "--", "/usr/bin/python3", "-B", LISTENER,
            "--profile", WORKLOAD_ID, "--port", str(PORT),
            "--requests", str(CASES),
            "--per-request-timeout", str(PER_REQUEST_TIMEOUT_SECONDS),
            "--deadline", str(DEADLINE_SECONDS),
            "--scope-unit", scope_unit(lease_id, generation),
            "--lease-id", lease_id, "--generation", str(generation))


def run(*, lease_id: str, generation: int, deadline_epoch: int,
        heartbeat: Callable[[], None], process_factory=subprocess.Popen,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        killpg=os.killpg, capture_root: str = "/run/local-ai-lab",
        expected_uid: int = 0) -> dict[str, object]:
    current = int(clock())
    if (type(deadline_epoch) is not int or deadline_epoch <= current
            or deadline_epoch > current + DEADLINE_SECONDS):
        raise AdapterError("candidate-g listener deadline is invalid")
    process = capture_dir = stdout_file = stderr_file = None
    try:
        root = os.path.abspath(capture_root)
        _prepare_capture_root(root, expected_uid=expected_uid)
        capture_dir = tempfile.mkdtemp(prefix="candidate-g-listener-", dir=root)
        _verify_capture_directory(capture_dir, expected_uid=expected_uid,
                                  label="capture directory")
        stdout_path = os.path.join(capture_dir, "stdout.json")
        stderr_path = os.path.join(capture_dir, "stderr.log")
        stdout_file = _open_capture_file(stdout_path, expected_uid=expected_uid)
        stderr_file = _open_capture_file(stderr_path, expected_uid=expected_uid)
        process = process_factory(listener_command(lease_id=lease_id, generation=generation),
                                  stdout=stdout_file, stderr=stderr_file,
                                  start_new_session=True)
        while True:
            heartbeat()
            if clock() >= deadline_epoch:
                raise AdapterError("candidate-g listener deadline reached")
            if (os.path.getsize(stdout_path) > RESULT_MAX_BYTES
                    or os.path.getsize(stderr_path) > RESULT_MAX_BYTES):
                raise AdapterError("candidate-g listener capture exceeded bound")
            status = process.poll()
            if status is not None:
                _verify_capture_file(stdout_path, expected_uid=expected_uid)
                _verify_capture_file(stderr_path, expected_uid=expected_uid)
                stdout_file.flush(); stderr_file.flush()
                stdout_file.close(); stderr_file.close()
                stdout_file = stderr_file = None
                with open(stdout_path, "rb") as stream:
                    stdout = stream.read(RESULT_MAX_BYTES + 1)
                with open(stderr_path, "rb") as stream:
                    stderr = stream.read(RESULT_MAX_BYTES + 1)
                if status != 0:
                    detail = bounded_guest_failure(stderr, stdout, status)
                    raise AdapterError("candidate-g listener exited nonzero: " + detail)
                if len(stdout) > RESULT_MAX_BYTES or len(stderr) > RESULT_MAX_BYTES:
                    raise AdapterError("candidate-g listener capture exceeded bound")
                try: result = json.loads(stdout.decode())
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise AdapterError("candidate-g listener output is not JSON") from exc
                try: validate_result(result)
                except TransactionError as exc: raise AdapterError(str(exc)) from exc
                return result
            sleep(min(1.0, max(0.0, deadline_epoch - clock())))
    finally:
        cleanup_error = None
        for handle in (stdout_file, stderr_file):
            if handle is not None:
                try: handle.close()
                except OSError: cleanup_error = cleanup_error or AdapterError("capture cleanup failed")
        if process is not None:
            try: _stop_process(process, killpg=killpg)
            except Exception as exc: cleanup_error = cleanup_error or exc
        if capture_dir is not None:
            try:
                _cleanup_capture(capture_dir,
                                 (os.path.join(capture_dir, "stdout.json"),
                                  os.path.join(capture_dir, "stderr.log")),
                                 expected_uid=expected_uid)
            except Exception as exc: cleanup_error = cleanup_error or exc
        if cleanup_error is not None: raise cleanup_error


if __name__ == "__main__":
    raise SystemExit("candidate-g listener adapter is source-only")
