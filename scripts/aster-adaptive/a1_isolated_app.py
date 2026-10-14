"""Fail-closed ASGI factory candidate for a separately isolated A1 sidecar.

This is source-only. It does not install a unit, acquire a lease, grant a key,
or assert that an LXC identity/network boundary exists. Host admission must
independently attest the deployed process before any benchmark request.
"""
from __future__ import annotations

import importlib
import hashlib
import json
import os
import re
import stat
from pathlib import Path

from a1_test_gateway import A1TestGateway, DurableAttemptJournal, REPO
from aster_asgi_clock import ASGIResponseClock

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
CLOCK_FIELDS = {"schema_version", "observation_id", "path", "http_status",
                "first_body_ms", "terminal_ms", "terminal_observed"}


def _owned(path: Path, uid: int, *, directory: bool) -> None:
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("invalid owner-only A1 path")
    resolved = path.resolve()
    if resolved == REPO or REPO in resolved.parents:
        raise ValueError("A1 evidence must stay outside Git")
    info = path.stat()
    if (info.st_uid != uid or info.st_mode & 0o077
            or (directory and not stat.S_ISDIR(info.st_mode))
            or (not directory and not stat.S_ISREG(info.st_mode))):
        raise ValueError("invalid owner-only A1 custody")


class DurableClockSink:
    """Append only allowlisted content-free ASGI rows and fsync each one."""

    def __init__(self, directory: Path, *, uid: int):
        _owned(directory, uid, directory=True)
        self.path = directory / "asgi-clock.jsonl"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        self.fd = os.open(self.path, flags, 0o600)

    def append(self, row: dict) -> None:
        if (not isinstance(row, dict) or set(row) != CLOCK_FIELDS
                or row.get("schema_version") != "aster-asgi-clock.v0"):
            raise ValueError("invalid content-free ASGI row")
        raw = (json.dumps(row, sort_keys=True, separators=(",", ":"),
                          allow_nan=False) + "\n").encode("utf-8")
        os.write(self.fd, raw)
        os.fsync(self.fd)

    def close(self) -> None:
        os.close(self.fd)


def _validated_config(config_path: Path, env: dict[str, str], uid: int) -> tuple[dict, bytes]:
    _owned(config_path, uid, directory=False)
    if env.get("ASTER_A1_TEST_MODE") != "isolated-20case":
        raise ValueError("A1 sidecar mode is not explicit")
    if env.get("ASTER_MAX_RESPONSE_TOKENS") != "256":
        raise ValueError("A1 output budget differs from frozen profile")
    if env.get("ASTER_MAX_TOOL_ROUNDS") != "0" or env.get("ASTER_REQUEST_TIMEOUT") != "60":
        raise ValueError("A1 tool and deadline bounds are not pinned")
    if env.get("ASTER_LLAMA_MODEL") != "qwen3.5-9b":
        raise ValueError("A1 upstream model is not pinned")
    if env.get("ASTER_LLAMA_BASE_URL") != "http://192.168.70.12:11435/v1":
        raise ValueError("A1 backend target is not pinned")
    if (env.get("ASTER_BROKER_APPROVAL_SOCKET") !=
            "/run/aster-a1-test/absent-approval.sock"
            or Path(env["ASTER_BROKER_APPROVAL_SOCKET"]).exists()
            or env.get("ASTER_OPENBAO_URL") != "http://127.0.0.1:1"
            or env.get("ASTER_NOTIFICATION_KEY") !=
            "/run/aster-a1-test/absent-vapid.pem"
            or Path(env["ASTER_NOTIFICATION_KEY"]).exists()
            or env.get("CREDENTIALS_DIRECTORY")):
        raise ValueError("A1 privileged path isolation is not pinned")
    knowledge = Path(env.get("ASTER_KNOWLEDGE_DIR", ""))
    _owned(knowledge, uid, directory=True)
    if any(knowledge.iterdir()):
        raise ValueError("A1 synthetic knowledge area is not empty")
    for name in ("ASTER_LAB_TARGETS", "ASTER_LAB_OWNER", "ASTER_LAB_WORKER_KEY",
                 "ASTER_ARR_BROKER_URL", "ASTER_ARR_BROKER_KEY",
                 "ASTER_BROKER_APPROVER_SUBJECT_HASHES", "ASTER_BROKER_PASSKEY_ACRS",
                 "ASTER_OPENBAO_UNSEAL_OWNER_HASHES"):
        if env.get(name):
            raise ValueError("privileged Aster setting present")
    if env.get("ASTER_SYSADMIN_DOCTOR_EVIDENCE", "").lower() in ("1", "true", "yes"):
        raise ValueError("connected incident evidence enabled")
    inner = env.get("ASTER_API_KEY", "").encode("ascii")
    backend = env.get("ASTER_LLAMA_API_KEY", "").encode("ascii")
    if (not 16 <= len(inner) <= 256 or not 16 <= len(backend) <= 256
            or inner == backend
            or any(not 33 <= value <= 126 for value in inner + backend)):
        raise ValueError("test credentials missing or reused")
    payload = json.loads(config_path.read_text())
    if (not isinstance(payload, dict) or set(payload) != {
            "schema_version", "ingress_token_sha256", "request_sha256s",
            "attempt_journal_dir", "clock_dir"}
            or payload["schema_version"] != "aster-a1-isolated-config.v0"
            or not isinstance(payload["ingress_token_sha256"], str)
            or not HEX64.fullmatch(payload["ingress_token_sha256"])
            or not isinstance(payload["request_sha256s"], list)
            or len(payload["request_sha256s"]) != 20
            or len(set(payload["request_sha256s"])) != 20
            or any(not isinstance(value, str) or not HEX64.fullmatch(value)
                   for value in payload["request_sha256s"])):
        raise ValueError("invalid A1 sidecar configuration")
    if hashlib.sha256(backend).hexdigest() == payload["ingress_token_sha256"]:
        raise ValueError("test credentials missing or reused")
    return payload, inner


def create_app(*, config_path: Path | None = None, env: dict[str, str] | None = None,
               uid: int | None = None, app_loader=None):
    """Assemble the guard after configuration checks, before importing Aster."""
    env = dict(os.environ if env is None else env)
    uid = os.geteuid() if uid is None else uid
    if uid == 0:
        raise ValueError("A1 sidecar must not run as root")
    config_path = config_path or Path(env.get("ASTER_A1_CONFIG", ""))
    payload, inner = _validated_config(config_path, env, uid)
    journal = DurableAttemptJournal(Path(payload["attempt_journal_dir"]))
    clock_directory = Path(payload["clock_dir"])
    sink = DurableClockSink(clock_directory, uid=uid)
    try:
        loader = app_loader or (lambda: importlib.import_module("aster_agent").app)
        aster = loader()
        return A1TestGateway(
            ASGIResponseClock(aster, sink),
            token_sha256=payload["ingress_token_sha256"],
            request_sha256s=frozenset(payload["request_sha256s"]),
            attempt_journal=journal,
            downstream_bearer=inner,
        )
    except BaseException:
        sink.close()
        raise
