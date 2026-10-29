"""Inactive fixed listener adapter for the SA3 Lab Hours workload."""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import tempfile
import time
from typing import Callable, Sequence

from sa3_expanded_quality_transaction import (DEADLINE_SECONDS,
    PER_REQUEST_TIMEOUT_SECONDS, RESULT_MAX_BYTES, TransactionError,
    validate_result)


WORKLOAD_ID = "sa3-expanded-source-quality-v1"
PORT = 11436
REQUEST_COUNT = 20
LISTENER = "/usr/local/sbin/aster-llama-lab-sa3"
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")


class AdapterError(RuntimeError):
    pass


CAPTURE_ROOT_MODE = 0o700
CAPTURE_FILE_MODE = 0o600


def _verify_capture_directory(path: str, *, expected_uid: int, label: str) -> None:
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise AdapterError(f"SA3 {label} custody is unavailable") from exc
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != expected_uid
            or stat.S_IMODE(info.st_mode) != CAPTURE_ROOT_MODE):
        raise AdapterError(f"SA3 {label} custody is invalid")


def _verify_capture_file(path: str, *, expected_uid: int) -> None:
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise AdapterError("SA3 capture file custody is unavailable") from exc
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != expected_uid
            or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != CAPTURE_FILE_MODE):
        raise AdapterError("SA3 capture file custody is invalid")


def _prepare_capture_root(path: str, *, expected_uid: int) -> None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        try:
            os.mkdir(path, CAPTURE_ROOT_MODE)
        except OSError as exc:
            raise AdapterError("SA3 capture root cannot be created") from exc
    except OSError as exc:
        raise AdapterError("SA3 capture root cannot be inspected") from exc
    _verify_capture_directory(path, expected_uid=expected_uid, label="capture root")


def _open_capture_file(path: str, *, expected_uid: int):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, CAPTURE_FILE_MODE)
        stream = os.fdopen(descriptor, "wb", buffering=0)
    except OSError as exc:
        raise AdapterError("SA3 capture file cannot be created") from exc
    try:
        _verify_capture_file(path, expected_uid=expected_uid)
    except Exception:
        stream.close()
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    stream.capture_path = path
    return stream


def _cleanup_capture(capture_dir: str, paths: tuple[str, ...], *, expected_uid: int) -> None:
    failures = []
    for path in paths:
        try:
            if os.path.lexists(path):
                try:
                    _verify_capture_file(path, expected_uid=expected_uid)
                except AdapterError:
                    failures.append("capture file custody drifted")
                os.unlink(path)
        except OSError:
            failures.append("capture file removal failed")
        if os.path.lexists(path):
            failures.append("capture file remains")
    try:
        os.rmdir(capture_dir)
    except OSError:
        failures.append("capture directory removal failed")
    if os.path.lexists(capture_dir):
        failures.append("capture directory remains")
    if failures:
        raise AdapterError("SA3 capture cleanup failed: " + "; ".join(dict.fromkeys(failures)))


def scope_unit(lease_id: str, generation: int) -> str:
    if not LEASE_RE.fullmatch(lease_id) or type(generation) is not int or generation < 1:
        raise AdapterError("SA3 listener lease identity is invalid")
    digest = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:16]
    return f"aster-llama-sa3-{digest}.scope"


def listener_command(*, lease_id: str, generation: int) -> tuple[str, ...]:
    """Return the only accepted LXC110 command; no booking command is accepted."""
    scope = scope_unit(lease_id, generation)
    return (
        "pct", "exec", "110", "--", LISTENER,
        "--profile", WORKLOAD_ID, "--port", str(PORT),
        "--requests", str(REQUEST_COUNT),
        "--per-request-timeout", str(PER_REQUEST_TIMEOUT_SECONDS),
        "--deadline", str(DEADLINE_SECONDS),
        "--scope-unit", scope,
        "--lease-id", lease_id, "--generation", str(generation),
    )


def _stop_process(process, *, killpg: Callable[[int, int], None] = os.killpg,
                  wait: Callable[..., object] | None = None) -> None:
    if process.poll() is not None:
        return
    try:
        killpg(process.pid, signal.SIGTERM)
    except (AttributeError, OSError):
        process.terminate()
    try:
        process.wait(timeout=5)
    except Exception:
        try:
            killpg(process.pid, signal.SIGKILL)
        except (AttributeError, OSError):
            process.kill()
        process.wait()


def run(*, lease_id: str, generation: int, deadline_epoch: int,
        heartbeat: Callable[[], None],
        process_factory: Callable[..., object] = subprocess.Popen,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        killpg: Callable[[int, int], None] = os.killpg,
        capture_root: str = "/run/local-ai-lab",
        expected_uid: int = 0) -> dict[str, object]:
    """Run only the fixed listener and return its validated result.

    This function is not wired into the installed reservation runner.  Its
    caller must provide the already-held lease heartbeat; it accepts no
    command, endpoint, model, credential or packet arguments.
    """
    current = int(clock())
    if (type(deadline_epoch) is not int or deadline_epoch <= current
            or deadline_epoch > current + DEADLINE_SECONDS):
        raise AdapterError("SA3 listener deadline is invalid")
    process = None
    capture_dir = None
    stdout_file = None
    stderr_file = None
    try:
        root = os.path.abspath(capture_root)
        _prepare_capture_root(root, expected_uid=expected_uid)
        capture_dir = tempfile.mkdtemp(prefix="sa3-listener-", dir=root)
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
                raise AdapterError("SA3 listener deadline reached")
            if os.path.getsize(stdout_path) > RESULT_MAX_BYTES:
                raise AdapterError("SA3 listener output exceeded bound")
            if os.path.getsize(stderr_path) > RESULT_MAX_BYTES:
                raise AdapterError("SA3 listener diagnostics exceeded bound")
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
                    raise AdapterError("SA3 listener exited nonzero")
                if len(stdout) > RESULT_MAX_BYTES:
                    raise AdapterError("SA3 listener output exceeded bound")
                if len(stderr) > RESULT_MAX_BYTES:
                    raise AdapterError("SA3 listener diagnostics exceeded bound")
                try:
                    result = json.loads(stdout.decode("utf-8"))
                except (TypeError, json.JSONDecodeError) as exc:
                    raise AdapterError("SA3 listener output is not JSON") from exc
                try:
                    validate_result(result)
                except TransactionError as exc:
                    raise AdapterError(str(exc)) from exc
                return result
            sleep(min(1.0, max(0.0, deadline_epoch - clock())))
    finally:
        cleanup_error = None
        if stdout_file is not None:
            try:
                stdout_file.close()
            except OSError as exc:
                cleanup_error = AdapterError("SA3 capture cleanup failed")
        if stderr_file is not None:
            try:
                stderr_file.close()
            except OSError as exc:
                cleanup_error = cleanup_error or AdapterError("SA3 capture cleanup failed")
        if process is not None:
            try:
                _stop_process(process, killpg=killpg)
            except Exception as exc:
                cleanup_error = cleanup_error or exc
        if capture_dir is not None:
            try:
                _cleanup_capture(
                    capture_dir,
                    (os.path.join(capture_dir, "stdout.json"),
                     os.path.join(capture_dir, "stderr.log")),
                    expected_uid=expected_uid)
            except Exception as exc:
                cleanup_error = cleanup_error or exc
        if cleanup_error is not None:
            raise cleanup_error


if __name__ == "__main__":
    raise SystemExit("SA3 listener adapter is an inactive source candidate")
