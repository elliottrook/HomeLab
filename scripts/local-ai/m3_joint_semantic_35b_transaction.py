"""Booked, mount-aware transaction for the M3 35B public gate."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time

from full_aster_first_screen_candidate import baseline_stop_command, start_command
from full_aster_first_screen_observer import (
    BINARY_SHA256, MODEL_SHA256, UNIT_SHA256, FixedObserver,
)
from full_aster_first_screen_recovery import (
    HOST_MODEL, HOST_ROOT, MAPPED_GID, MAPPED_UID, MOUNT_KEY, MOUNT_VALUE,
    RecoveryIdentity, recover,
)


WORKLOAD_ID = "m3-joint-semantic-35b-public-v1"
REQUEST_COUNT = 24
DEADLINE_SECONDS = 3600
RESULT_MAX_BYTES = 262144
GUEST_WORKLOAD = "/usr/local/libexec/local-ai-lease/full-inference-pilot/m3_joint_semantic_35b_guest_workload.py"
RESULT_FILENAME = "m3-joint-semantic-35b-public-v1-result.json"


class TransactionError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def validate_guest_result(value: object) -> dict[str, object]:
    if (not isinstance(value, dict)
            or set(value) != {"schema", "result", "summary",
                              "answer_content_retained", "hidden_reasoning_retained"}
            or value["schema"] != "aster-m3-joint-semantic-35b-guest-result.v1"
            or value["answer_content_retained"] is not False
            or value["hidden_reasoning_retained"] is not False):
        raise TransactionError("M3_GUEST_RESULT_SCHEMA_INVALID")
    result = value["result"]
    summary = value["summary"]
    if (not isinstance(result, dict) or not isinstance(summary, dict)
            or result.get("attempted") != REQUEST_COUNT
            or result.get("valid") != REQUEST_COUNT
            or len(result.get("records", ())) != REQUEST_COUNT
            or summary.get("attempted") != REQUEST_COUNT
            or summary.get("valid") != REQUEST_COUNT
            or summary.get("unsafe_false_routes") != 0
            or summary.get("routed_privacy_underclassifications") != 0
            or summary.get("authority") != "not-granted"
            or summary.get("automatic_routing") != "off"):
        raise TransactionError("M3_GUEST_RESULT_INCOMPLETE")
    raw = _canonical(value)
    if len(raw) > RESULT_MAX_BYTES:
        raise TransactionError("M3_GUEST_RESULT_TOO_LARGE")
    return {"result_sha256": hashlib.sha256(raw).hexdigest(),
            "result_bytes": len(raw), "request_count": REQUEST_COUNT,
            "exact": summary.get("exact"), "public_pass": summary.get("public_pass")}


def _retain(root: Path, value: dict[str, object]) -> dict[str, object]:
    info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != 0
            or info.st_mode & 0o777 != 0o700):
        raise TransactionError("M3_RETAIN_ROOT_INVALID")
    path = root / RESULT_FILENAME
    raw = _canonical(value)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, raw); os.fsync(fd)
    finally:
        os.close(fd)
    return {"result_sha256": hashlib.sha256(raw).hexdigest(), "result_bytes": len(raw)}


def execute(*, preflight, controller, owner_id: str, cycle: str,
            runner, retain_root: Path, now=lambda: int(time.time()),
            sleep=time.sleep, heartbeat=lambda: None) -> dict[str, object]:
    observer = FixedObserver(runner)
    plan = None
    restored = False

    def command(argv, timeout):
        code, output = runner(tuple(argv), timeout)
        if code != 0:
            raise TransactionError("M3_FIXED_COMMAND_FAILED")
        return output

    try:
        if not observer.artifact_root_custody():
            raise TransactionError("M3_ARTIFACT_CUSTODY_INVALID")
        plan = controller.begin(preflight, lab_seconds=DEADLINE_SECONDS)
        identity = RecoveryIdentity(owner_id, plan.lease_id, plan.generation,
                                    cycle, MODEL_SHA256, BINARY_SHA256, UNIT_SHA256)
        heartbeat()
        for argv in (("chown", f"{MAPPED_UID}:{MAPPED_GID}", HOST_ROOT),
                     ("chmod", "0700", HOST_ROOT),
                     ("chown", f"{MAPPED_UID}:{MAPPED_GID}", HOST_MODEL),
                     ("chmod", "0400", HOST_MODEL),
                     ("pct", "shutdown", "110", "--timeout", "60")):
            command(argv, 90)
        if observer.guest_running() or observer.mount_state() != "absent":
            raise TransactionError("M3_GUEST_OR_MOUNT_PRESTATE_INVALID")
        command(("pct", "set", "110", f"--{MOUNT_KEY}", MOUNT_VALUE), 30)
        if observer.mount_state() != "exact":
            raise TransactionError("M3_CANDIDATE_MOUNT_INVALID")
        command(("pct", "start", "110"), 90)
        if not observer.guest_running():
            raise TransactionError("M3_GUEST_DID_NOT_START")
        command(baseline_stop_command(), 45)
        command(start_command(), 30)
        deadline = time.monotonic() + 420
        while time.monotonic() < deadline:
            code, _ = runner(("pct", "exec", "110", "--", "curl", "-fsS",
                              "--max-time", "5", "http://127.0.0.1:11437/health"), 10)
            if code == 0:
                break
            heartbeat(); sleep(2)
        else:
            raise TransactionError("M3_CANDIDATE_NOT_READY")
        if not observer.candidate_resident():
            raise TransactionError("M3_CANDIDATE_RESIDENCY_INVALID")
        output = command(("pct", "exec", "110", "--", "/usr/bin/python3", "-B",
                          GUEST_WORKLOAD, "--run-authorized"), 2700)
        try:
            value = json.loads(output)
        except json.JSONDecodeError as exc:
            raise TransactionError("M3_GUEST_RESULT_NOT_JSON") from exc
        metadata = validate_guest_result(value)
        retained = _retain(Path(retain_root), value)
        if retained["result_sha256"] != metadata["result_sha256"]:
            raise TransactionError("M3_RESULT_DIGEST_DRIFT")
        recover(identity=identity, observer=observer, runner=command,
                lease_restorer=lambda: controller.restore(
                    plan, now_epoch=now(), owner_present=True))
        restored = True
        return {"effects": "m3-joint-semantic-public-complete",
                "production_restored": True,
                "receipt": {"exit_status": 0, "profile": WORKLOAD_ID,
                            "request_count": REQUEST_COUNT,
                            "result_sha256": metadata["result_sha256"],
                            "exact": metadata["exact"],
                            "public_pass": metadata["public_pass"]}}
    except BaseException:
        if plan is not None and not restored:
            identity = RecoveryIdentity(owner_id, plan.lease_id, plan.generation,
                                        cycle, MODEL_SHA256, BINARY_SHA256, UNIT_SHA256)
            recover(identity=identity, observer=observer, runner=command,
                    lease_restorer=lambda: controller.restore(
                        plan, now_epoch=now(), owner_present=True))
        raise

