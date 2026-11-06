#!/usr/bin/env python3
"""Install or roll back bounded Aster Remote last-room persistence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile
import urllib.error
import urllib.request


HOST = "hermesagent"
TARGET = Path("/opt/aster-agent/static/remote")
CHECKPOINT = Path("/var/lib/aster/checkpoints/astertv-v3-m8-remote-room-preference-20261105")
FILES = ("app.js", "sw.js")
OLD = {
    "app.js": "c4b3b371c18a7b3f53dad298ad8440f303b47f8c9c96cafbbb5c4c364e0df52b",
    "sw.js": "4011c0bd123a743937a6d9053ad44d1da15c7ac646ddc50cbf401b38cbd94968",
}
NEW = {
    "app.js": "76a14595af2da756a72975eb02afe45cd21ac035d8b118dfc67a2635258e0762",
    "sw.js": "9be36dd12a332cf22c71c3364479b23623b2a10abb07b8be0a5f8c27bc0f2bc8",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_hashes(root: Path, expected: dict[str, str]) -> None:
    for name, value in expected.items():
        path = root / name
        if not path.is_file() or digest(path) != value:
            raise RuntimeError(f"remote-room-preference-drift:{name}")


def atomic_copy(source: Path, destination: Path) -> None:
    stat = destination.stat()
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(descriptor)
    temporary_path = Path(temporary)
    try:
        shutil.copyfile(source, temporary_path)
        os.chown(temporary_path, stat.st_uid, stat.st_gid)
        os.chmod(temporary_path, stat.st_mode & 0o777)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def checkpoint() -> None:
    if CHECKPOINT.exists():
        raise RuntimeError("remote-room-preference-checkpoint-exists")
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    for name in FILES:
        shutil.copy2(TARGET / name, CHECKPOINT / name)
    (CHECKPOINT / "manifest.json").write_text(
        json.dumps({"schema": 1, "host": HOST, "files": OLD}, sort_keys=True) + "\n"
    )
    os.chmod(CHECKPOINT / "manifest.json", 0o600)
    assert_hashes(CHECKPOINT, OLD)


def route_hash(path: str) -> str:
    with urllib.request.urlopen("http://192.168.70.10:9120" + path, timeout=4) as response:
        if response.status != 200:
            raise RuntimeError(f"remote-room-preference-route:{path}")
        return hashlib.sha256(response.read()).hexdigest()


def validate(expected: dict[str, str]) -> None:
    assert_hashes(TARGET, expected)
    for name in FILES:
        if route_hash("/remote/" + name) != expected[name]:
            raise RuntimeError(f"remote-room-preference-http-drift:{name}")
    request = urllib.request.Request("http://192.168.70.10:9120/v1/remote/session")
    try:
        urllib.request.urlopen(request, timeout=4)
    except urllib.error.HTTPError as error:
        if error.code == 403:
            return
    raise RuntimeError("remote-room-preference-auth-regression")


def restore() -> None:
    assert_hashes(CHECKPOINT, OLD)
    for name in FILES:
        atomic_copy(CHECKPOINT / name, TARGET / name)
    validate(OLD)


def install(source: Path) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-room-preference-wrong-target")
    assert_hashes(source, NEW)
    assert_hashes(TARGET, OLD)
    checkpoint()
    try:
        for name in FILES:
            atomic_copy(source / name, TARGET / name)
        validate(NEW)
    except Exception:
        restore()
        raise
    print(json.dumps({"outcome": "installed", "checkpoint": str(CHECKPOINT),
                      "service_restart": False}, sort_keys=True))


def rollback() -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-room-preference-wrong-target")
    assert_hashes(TARGET, NEW)
    restore()
    print(json.dumps({"outcome": "rolled-back", "checkpoint": str(CHECKPOINT),
                      "service_restart": False}, sort_keys=True))


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--source", type=Path)
group.add_argument("--rollback", action="store_true")
arguments = parser.parse_args()
rollback() if arguments.rollback else install(arguments.source)
