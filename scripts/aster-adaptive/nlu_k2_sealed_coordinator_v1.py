"""Mac mini coordinator for one preregistered K2 sealed transaction."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import time

import nlu_k2_sealed_transaction_preregistration_v1 as preregistration
from nlu_threshold_policy import decode_unique_json


PREREGISTRATION_SHA256 = __import__("hashlib").sha256(
    preregistration.canonical(preregistration.artifact())).hexdigest()
WORKLOAD_ID = "m3-k2-sealed-evaluation-v1"
RUNTIME_ROOT = Path("/private/tmp/aster-k2-sealed-coordinator-runtime-v1")
MACBOOK_WRAPPER = (
    "/private/tmp/aster-k2-sealed-runtime-v1/"
    "nlu_k2_sealed_macbook_wrapper_v1.py"
)
BOOKING_ID = re.compile(
    r"aster-stream-a-m3-k2-sealed-[0-9]{8}-[0-9]{4}-r[1-9][0-9]*\Z"
)
SESSION_ID = re.compile(r"k2-sealed-[0-9a-f]{16}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class CoordinatorError(RuntimeError):
    pass


def validate_session(value: object, *, now_epoch: int) -> dict[str, object]:
    keys = {
        "schema", "state", "workload_id", "booking_id",
        "preregistration_sha256", "session_id", "lease_id", "generation",
        "start_epoch", "deadline_epoch", "request_count", "retries",
        "relay_nonce_sha256", "upstream_nonce_sha256",
        "private_listener_port", "private_listener_scope",
        "production_masked", "operation_lock_held", "authority",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-m3-k2-sealed-session.v1"
            or value.get("state") != "ready"
            or value.get("workload_id") != WORKLOAD_ID
            or not isinstance(value.get("booking_id"), str)
            or BOOKING_ID.fullmatch(value["booking_id"]) is None
            or value.get("preregistration_sha256") != PREREGISTRATION_SHA256
            or not isinstance(value.get("session_id"), str)
            or SESSION_ID.fullmatch(value["session_id"]) is None
            or type(value.get("start_epoch")) is not int
            or type(value.get("deadline_epoch")) is not int
            or not value["start_epoch"] <= now_epoch < value["deadline_epoch"]
            or value["deadline_epoch"] - value["start_epoch"] != 1800
            or value.get("request_count") != 32
            or value.get("retries") != 0
            or value.get("private_listener_port") != 11436
            or value.get("production_masked") is not True
            or value.get("operation_lock_held") is not True
            or value.get("authority") != "not-granted"):
        raise CoordinatorError("K2 sealed coordinator session changed")
    for field in ("relay_nonce_sha256", "upstream_nonce_sha256"):
        if (not isinstance(value.get(field), str)
                or HEX64.fullmatch(value[field]) is None):
            raise CoordinatorError("K2 sealed coordinator nonce hash changed")
    if value["relay_nonce_sha256"] == value["upstream_nonce_sha256"]:
        raise CoordinatorError("K2 sealed coordinator nonces are not distinct")
    return value


def _token(path: Path, digest: str, *, expected_uid: int | None = None) -> str:
    uid = os.geteuid() if expected_uid is None else expected_uid
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink()
            or info.st_uid != uid or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600):
        raise CoordinatorError("K2 sealed coordinator nonce custody changed")
    raw = path.read_bytes()
    import hashlib
    if hashlib.sha256(raw).hexdigest() != digest:
        raise CoordinatorError("K2 sealed coordinator nonce digest changed")
    if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise CoordinatorError("K2 sealed coordinator nonce shape changed")
    try:
        value = raw[:-1].decode("ascii")
    except UnicodeDecodeError as exc:
        raise CoordinatorError("K2 sealed coordinator nonce encoding changed") from exc
    if not 32 <= len(value) <= 256 or any(not 33 <= ord(c) <= 126 for c in value):
        raise CoordinatorError("K2 sealed coordinator nonce value changed")
    return value


def commands(session_id: str, relay_token_file: Path,
             upstream_token_file: Path,
             runtime_root: Path = RUNTIME_ROOT) -> dict[str, tuple[str, ...]]:
    if SESSION_ID.fullmatch(session_id) is None:
        raise CoordinatorError("K2 sealed coordinator session identity changed")
    ssh_options = ("-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes",
                   "-o", "ServerAliveInterval=5", "-o", "ServerAliveCountMax=3")
    return {
        "upstream_tunnel": (
            "ssh", "-N", *ssh_options,
            "-L", "127.0.0.1:11439:192.168.70.12:11436",
            "root@192.168.50.10"),
        "relay": (
            "/usr/bin/python3", "-B",
            str(runtime_root / "nlu_k2_sealed_relay_v1.py"),
            "--relay-token-file", str(relay_token_file),
            "--upstream-token-file", str(upstream_token_file)),
        "reverse_tunnel": (
            "ssh", "-N", *ssh_options,
            "-R", "127.0.0.1:11437:127.0.0.1:11438", "macbook"),
        "reverse_probe": (
            "ssh", "-o", "BatchMode=yes", "macbook", "/usr/bin/nc", "-z",
            "-G", "2", "127.0.0.1", "11437"),
        "macbook_wrapper": (
            "ssh", "-o", "BatchMode=yes", "macbook", "/usr/bin/python3",
            "-B", MACBOOK_WRAPPER, "--session-id", session_id),
    }


def _wait_port(port: int, processes: list, *, clock=time.monotonic,
               sleep=time.sleep, timeout: float = 10.0) -> None:
    end = clock() + timeout
    while clock() < end:
        if any(process.poll() is not None for process in processes):
            raise CoordinatorError("K2 sealed coordinator child exited early")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            sleep(0.1)
    raise CoordinatorError("K2 sealed coordinator loopback port unavailable")


def _stop(process) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _wait_reverse(command: tuple[str, ...], children: list, *,
                  command_runner=subprocess.run, clock=time.monotonic,
                  sleep=time.sleep, timeout: float = 10.0) -> None:
    end = clock() + timeout
    while clock() < end:
        if any(process.poll() is not None for process in children):
            raise CoordinatorError("K2 sealed coordinator child exited early")
        probe = command_runner(command, capture_output=True,
                               timeout=5, check=False)
        if probe.returncode == 0:
            return
        sleep(0.2)
    raise CoordinatorError("K2 sealed reverse tunnel unavailable")


def execute(*, session_raw: bytes, relay_token_file: Path,
            upstream_token_file: Path, process_factory=subprocess.Popen,
            command_runner=subprocess.run, clock=time.time,
            monotonic=time.monotonic, sleep=time.sleep,
            runtime_root: Path = RUNTIME_ROOT,
            expected_uid: int | None = None) -> dict[str, object]:
    session = validate_session(decode_unique_json(session_raw),
                               now_epoch=int(clock()))
    relay_token = _token(relay_token_file, session["relay_nonce_sha256"],
                         expected_uid=expected_uid)
    _token(upstream_token_file, session["upstream_nonce_sha256"],
           expected_uid=expected_uid)
    plan = commands(session["session_id"], relay_token_file,
                    upstream_token_file, runtime_root=runtime_root)
    children = []
    relay = None
    try:
        upstream = process_factory(plan["upstream_tunnel"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   start_new_session=True)
        children.append(upstream)
        _wait_port(11439, children, clock=monotonic, sleep=sleep)
        relay = process_factory(plan["relay"], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        children.append(relay)
        _wait_port(11438, children, clock=monotonic, sleep=sleep)
        reverse = process_factory(plan["reverse_tunnel"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  start_new_session=True)
        children.append(reverse)
        _wait_reverse(plan["reverse_probe"], children,
                      command_runner=command_runner,
                      clock=monotonic, sleep=sleep)
        completed = command_runner(
            plan["macbook_wrapper"], input=(relay_token + "\n").encode(),
            capture_output=True, timeout=1800, check=False)
        if completed.returncode != 0:
            raise CoordinatorError("K2 sealed MacBook wrapper failed")
        value = decode_unique_json(completed.stdout)
        keys = {"schema", "state", "session_id", "model_requests", "retries",
                "response_errors", "status", "records_sha256",
                "metrics_sha256", "journal_sha256", "authority"}
        if (not isinstance(value, dict) or set(value) != keys
                or value.get("schema")
                    != "aster-nlu-k2-sealed-macbook-result.v1"
                or value.get("state") != "complete"
                or value.get("session_id") != session["session_id"]
                or value.get("model_requests") != 32
                or value.get("retries") != 0
                or value.get("response_errors") != 0
                or value.get("status") not in {"pass", "reject"}
                or value.get("authority") != "not-granted"
                or any(not isinstance(value.get(field), str)
                       or HEX64.fullmatch(value[field]) is None
                       for field in ("records_sha256", "metrics_sha256",
                                     "journal_sha256"))):
            raise CoordinatorError("K2 sealed MacBook result changed")
        relay_stdout, _relay_stderr = relay.communicate(timeout=10)
        relay_value = decode_unique_json(relay_stdout)
        if (relay.returncode != 0
                or relay_value != {
                    "schema": "aster-nlu-k2-sealed-relay-summary.v1",
                    "state": "complete", "requests": 32, "retries": 0,
                    "failure_code": None, "authority": "not-granted"}):
            raise CoordinatorError("K2 sealed relay result changed")
        return {"schema": "aster-nlu-k2-sealed-coordinator-result.v1",
                "state": "complete", "booking_id": session["booking_id"],
                "session_id": session["session_id"], "model_requests": 32,
                "retries": 0, "response_errors": 0,
                "status": value["status"],
                "records_sha256": value["records_sha256"],
                "metrics_sha256": value["metrics_sha256"],
                "journal_sha256": value["journal_sha256"],
                "authority": "not-granted"}
    finally:
        for process in reversed(children):
            _stop(process)
        for path in (relay_token_file, upstream_token_file):
            if os.path.lexists(path):
                path.unlink()
            if os.path.lexists(path):
                raise CoordinatorError("K2 sealed coordinator nonce cleanup failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--relay-token-file", type=Path, required=True)
    parser.add_argument("--upstream-token-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = execute(session_raw=args.session.read_bytes(),
                         relay_token_file=args.relay_token_file,
                         upstream_token_file=args.upstream_token_file)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (CoordinatorError, OSError, ValueError,
            subprocess.SubprocessError) as exc:
        print(json.dumps({"schema": "aster-nlu-k2-sealed-coordinator-result.v1",
                          "state": "no_go", "failure_class": type(exc).__name__,
                          "authority": "not-granted"},
                         sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
