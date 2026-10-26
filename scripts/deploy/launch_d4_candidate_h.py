#!/usr/bin/python3
"""Exact, fail-closed descriptor launcher for the unapproved D4 candidate-H."""

from __future__ import annotations

import grp
import hashlib
import os
from pathlib import Path
import pwd
import signal
import stat
import subprocess
import sys


PACKET_DIR = Path("/var/lib/aster/d4-candidate-h")
OUTPUT_DIR = Path("/var/lib/aster/d4-candidate-h-output")
ENV_FILE = Path("/etc/aster/aster.env")
EVAL_USER = "aster-d4-eval"
EVAL_UID = 977
EVAL_GID = 977
INTERPRETER = Path("/opt/aster-agent/venv/bin/python")
INTERPRETER_TARGET = Path("/usr/bin/python3.13")
INTERPRETER_SHA256 = "889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9"
RUN_DIGEST = "423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4"
LEDGER = OUTPUT_DIR / "attempt-journal.jsonl"
MAX_ENV_BYTES = 65536
MAX_KEY_BYTES = 4096
TIMEOUT_SECONDS = 2200

FILES = {
    "sa3_development_execute.py": (8191, "af925aeae2197ac27dfb787775f7706c40712147eabdd0825551f62002b6ae5a"),
    "sa3_fair_request.py": (3221, "048573965c474a21f03baf4ce76d2e75c8e78b61f3086db943b78d612209c9ea"),
    "sa3_fresh_execute.py": (5430, "3294e86a1d970ff8f4ba61859f21e0828f30a0c79c08e9ae817957bb5c5150dc"),
    "sa3_fresh_package.py": (18546, "6abe578c67974d156e1a04e4a50672c31dc160e1034a6ebf667061e24f2b4eeb"),
    "sa3_investigation.py": (14655, "40f5525ed2a893afb1bffdd7f3243218b943573635ed116331ea0230707ba877"),
    "sa3_investigation_runner.py": (4284, "448e3e428f5a7d187f5ec178a12e5f17ec4fac0ae859f78df08ff2b066be62b9"),
    "validate_sa3_fixture_bundle.py": (4890, "57c9a9edac398dbeeb90747d8c6582d2e4282e0b74fd6618e01fae48b58ef31d"),
    "validate_sa3_holdout_release.py": (4497, "64b5344243bf99e11c81bd058f23ee0cf63f1a17de133e8326fcde44a97840c7"),
    "sysadmin-sa3-development-fixtures-draft-v1.json": (25303, "c3999bdd26d66290fb751519fc2439d28f45bc9fde4e13a76bc6a1afae4faf58"),
    "sysadmin-incident-development-extension-draft-v1.json": (18711, "85e511b8470bbfb753f30668c1589259e73518d92b1e281008aaa7bd0cc0fbbb"),
    "sysadmin-incident-development-plan-v1.json": (802, "387fdf869d697295fea17736c14241f94b6c62af92067cd91d8fa4555da50791"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, *, uid: int, gid: int, mode: int) -> os.stat_result:
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise ValueError(f"{path.name}: regular non-symlink file required")
    if (metadata.st_uid, metadata.st_gid, stat.S_IMODE(metadata.st_mode)) != (
        uid, gid, mode
    ):
        raise ValueError(f"{path.name}: custody mismatch")
    return metadata


def validate_eval_identity() -> tuple[int, int]:
    account = pwd.getpwnam(EVAL_USER)
    group = grp.getgrnam(EVAL_USER)
    if (account.pw_uid, account.pw_gid, group.gr_gid) != (
        EVAL_UID, EVAL_GID, EVAL_GID
    ):
        raise ValueError("candidate evaluation identity mismatch")
    if account.pw_shell not in ("/usr/sbin/nologin", "/sbin/nologin"):
        raise ValueError("candidate evaluation identity must be non-login")
    if set(os.getgrouplist(EVAL_USER, EVAL_GID)) != {EVAL_GID}:
        raise ValueError("candidate evaluation identity has supplementary groups")
    return account.pw_uid, account.pw_gid


def validate_packet(
    root: Path = PACKET_DIR, *, uid: int = 0, gid: int = EVAL_GID
) -> None:
    metadata = root.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or root.is_symlink():
        raise ValueError("candidate packet must be a non-symlink directory")
    if (metadata.st_uid, metadata.st_gid, stat.S_IMODE(metadata.st_mode)) != (
        uid, gid, 0o750
    ):
        raise ValueError("candidate packet custody mismatch")
    if {entry.name for entry in os.scandir(root)} != set(FILES):
        raise ValueError("candidate packet file set mismatch")
    for name, (expected_size, expected_digest) in FILES.items():
        path = root / name
        metadata = require_file(path, uid=uid, gid=gid, mode=0o640)
        if metadata.st_size != expected_size or sha256_file(path) != expected_digest:
            raise ValueError(f"{name}: identity mismatch")


def validate_output_directory(
    root: Path = OUTPUT_DIR, *, uid: int = EVAL_UID, gid: int = EVAL_GID
) -> None:
    metadata = root.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or root.is_symlink():
        raise ValueError("candidate output must be a non-symlink directory")
    if (metadata.st_uid, metadata.st_gid, stat.S_IMODE(metadata.st_mode)) != (
        uid, gid, 0o700
    ):
        raise ValueError("candidate output custody mismatch")
    with os.scandir(root) as entries:
        if next(entries, None) is not None:
            raise ValueError("candidate output directory must be empty")


def validate_interpreter() -> None:
    if INTERPRETER.resolve(strict=True) != INTERPRETER_TARGET:
        raise ValueError("candidate interpreter target mismatch")
    metadata = require_file(INTERPRETER_TARGET, uid=0, gid=0, mode=0o755)
    if metadata.st_size <= 0 or sha256_file(INTERPRETER_TARGET) != INTERPRETER_SHA256:
        raise ValueError("candidate interpreter identity mismatch")


def read_key_bytes(
    path: Path = ENV_FILE, *, uid: int = 0, gid: int | None = None
) -> bytearray:
    expected_gid = grp.getgrnam("aster").gr_gid if gid is None else gid
    require_file(path, uid=uid, gid=expected_gid, mode=0o640)
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_uid, opened.st_gid, stat.S_IMODE(opened.st_mode))
            != (uid, expected_gid, 0o640)
        ):
            raise ValueError("credential file custody changed during open")
        if opened.st_size <= 0 or opened.st_size > MAX_ENV_BYTES:
            raise ValueError("credential file has invalid bounded size")
        raw = bytearray()
        while len(raw) < opened.st_size:
            chunk = os.read(descriptor, opened.st_size - len(raw))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) != opened.st_size or os.read(descriptor, 1):
            raise ValueError("credential file changed during bounded read")
    finally:
        os.close(descriptor)
    try:
        prefix = b"ASTER_LLAMA_API_KEY="
        matches: list[bytearray] = []
        position = 0
        while position < len(raw):
            end = raw.find(b"\n", position)
            if end < 0:
                end = len(raw)
            if raw[position:position + len(prefix)] == prefix:
                matches.append(bytearray(raw[position + len(prefix):end]))
            position = end + 1
        if len(matches) != 1:
            for match in matches:
                match[:] = b"\0" * len(match)
            raise ValueError("credential file must contain exactly one API key")
        value = matches[0]
        if len(value) >= 2 and value[:1] == value[-1:] and value[:1] in (b"'", b'"'):
            value.pop()
            del value[0]
        if (
            not value
            or len(value) > MAX_KEY_BYTES
            or any(byte <= 32 or byte >= 127 for byte in value)
        ):
            value[:] = b"\0" * len(value)
            raise ValueError("credential value has invalid encoding")
        return value
    finally:
        for index in range(len(raw)):
            raw[index] = 0


def run_with_key_fd(
    argv: list[str], secret: bytearray, *, timeout: int,
    child_uid: int | None = EVAL_UID, child_gid: int | None = EVAL_GID,
) -> int:
    read_fd, write_fd = os.pipe()
    os.set_inheritable(read_fd, False)
    os.set_inheritable(write_fd, False)
    try:
        if os.write(write_fd, secret) != len(secret):
            raise RuntimeError("credential descriptor write was incomplete")
        os.close(write_fd)
        write_fd = -1
        command = [*argv, "--key-fd", str(read_fd)]
        environment = {
            name: os.environ[name]
            for name in (
                "PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "TZ",
                "__CF_USER_TEXT_ENCODING",
            )
            if name in os.environ
        }
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        identity = {}
        if child_uid is not None or child_gid is not None:
            if child_uid is None or child_gid is None:
                raise ValueError("complete child identity required")
            identity = {
                "user": child_uid,
                "group": child_gid,
                "extra_groups": (),
                "umask": 0o077,
            }
        process = subprocess.Popen(
            command, cwd=PACKET_DIR, env=environment, pass_fds=(read_fd,),
            start_new_session=True, **identity,
        )
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            return 124
    finally:
        for descriptor in (read_fd, write_fd):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        for index in range(len(secret)):
            secret[index] = 0


def main() -> int:
    if os.geteuid() != 0:
        raise SystemExit("root execution identity required")
    eval_uid, eval_gid = validate_eval_identity()
    validate_packet(gid=eval_gid)
    validate_output_directory(uid=eval_uid, gid=eval_gid)
    validate_interpreter()
    secret = read_key_bytes()
    command = [
        str(INTERPRETER),
        str(PACKET_DIR / "sa3_development_execute.py"),
        "--fixtures", str(PACKET_DIR / "sysadmin-sa3-development-fixtures-draft-v1.json"),
        "--source-corpus", str(PACKET_DIR / "sysadmin-incident-development-extension-draft-v1.json"),
        "--source-plan", str(PACKET_DIR / "sysadmin-incident-development-plan-v1.json"),
        "--expected-run-digest", RUN_DIGEST,
        "--ledger", str(LEDGER),
        "--execute",
    ]
    return run_with_key_fd(
        command, secret, timeout=TIMEOUT_SECONDS,
        child_uid=eval_uid, child_gid=eval_gid,
    )


if __name__ == "__main__":
    raise SystemExit(main())
