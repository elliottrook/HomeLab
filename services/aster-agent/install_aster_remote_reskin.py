#!/usr/bin/env python3
"""Install or roll back the bounded Aster Remote static reskin."""

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
CHECKPOINT = Path("/var/lib/aster/checkpoints/astertv-v3-m8-remote-reskin-20261105")
FILES = ("index.html", "styles.css", "app.js", "sw.js")
OLD = {
    "index.html": "37f77ed36bb5f9d0c7ca857e4395469ceb74d155760c5ea9a1f913f243c39570",
    "styles.css": "0493afafca4bafebc8c886209646c47cf1fb9ce52cf586265050dedd35de941e",
    "app.js": "4764929e4b8c52c7f3c35a1ee6f1b0a6d4b2104418992b6ff4cf3d24a2d3745d",
    "sw.js": "e0c1fce48c5c35edd14447c46406c9299a53b51fee21b92b6250d075b7caf381",
}
NEW = {
    "index.html": "66dd4cb297431268e52849e40c1bc9d710b5dfdf59fded06ce322d30107a1fba",
    "styles.css": "fd6fe2d6dfb05ef78f56006150af5f6ec499110813bbf65f62928d6ff684ff43",
    "app.js": "420e47015e9dd5fcfb1ef0934381597acbeb313d0375a56a1b3791693a673258",
    "sw.js": "3c54a84f9294aec06a86189e750b3b850e02ea3ad88522f5a43e97e097285c58",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_hashes(root: Path, expected: dict[str, str]) -> None:
    for name, value in expected.items():
        path = root / name
        if not path.is_file() or digest(path) != value:
            raise RuntimeError(f"remote-reskin-drift:{name}")


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
        raise RuntimeError("remote-reskin-checkpoint-exists")
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    for name in FILES:
        shutil.copy2(TARGET / name, CHECKPOINT / name)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({"schema": 1, "host": HOST, "files": OLD}, sort_keys=True) + "\n")
    os.chmod(CHECKPOINT / "manifest.json", 0o600)
    assert_hashes(CHECKPOINT, OLD)


def route_hash(path: str) -> str:
    with urllib.request.urlopen("http://192.168.70.10:9120" + path, timeout=4) as response:
        if response.status != 200:
            raise RuntimeError(f"remote-reskin-route:{path}")
        return hashlib.sha256(response.read()).hexdigest()


def validate(expected: dict[str, str]) -> None:
    assert_hashes(TARGET, expected)
    routes = {"/remote/": "index.html", "/remote/styles.css": "styles.css", "/remote/app.js": "app.js", "/remote/sw.js": "sw.js"}
    for route, name in routes.items():
        if route_hash(route) != expected[name]:
            raise RuntimeError(f"remote-reskin-http-drift:{name}")
    request = urllib.request.Request("http://192.168.70.10:9120/v1/remote/session")
    try:
        urllib.request.urlopen(request, timeout=4)
    except urllib.error.HTTPError as error:
        if error.code == 401:
            return
    raise RuntimeError("remote-reskin-auth-regression")


def restore() -> None:
    assert_hashes(CHECKPOINT, OLD)
    for name in FILES:
        atomic_copy(CHECKPOINT / name, TARGET / name)
    validate(OLD)


def install(source: Path) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-reskin-wrong-target")
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
    print(json.dumps({"outcome": "installed", "checkpoint": str(CHECKPOINT), "service_restart": False}, sort_keys=True))


def rollback() -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-reskin-wrong-target")
    assert_hashes(TARGET, NEW)
    restore()
    print(json.dumps({"outcome": "rolled-back", "checkpoint": str(CHECKPOINT), "service_restart": False}, sort_keys=True))


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--source", type=Path)
group.add_argument("--rollback", action="store_true")
arguments = parser.parse_args()
rollback() if arguments.rollback else install(arguments.source)
