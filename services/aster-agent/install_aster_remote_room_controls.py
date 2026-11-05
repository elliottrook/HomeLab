#!/usr/bin/env python3
"""Install or roll back the Aster Remote identity and room-control layout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Dict, Optional
import urllib.error
import urllib.request


HOST = "hermesagent"
STATIC_TARGET = Path("/opt/aster-agent/static/remote")
MODULE_TARGET = Path("/opt/aster-agent/aster_remote.py")
CHECKPOINT = Path("/var/lib/aster/checkpoints/astertv-v3-m8-remote-room-controls-20261105-r2")
OLD_MODULE = "17d7e1f0f76f284195e8ac82cbc7e3a222ebd6d7704bc5ed86b6a9d691b16eba"
NEW_MODULE = "02722c5039ae4a87eeff612c60c4ccc5431d033115d3ac40a0583f6631629809"
OLD = {
    "index.html": "66dd4cb297431268e52849e40c1bc9d710b5dfdf59fded06ce322d30107a1fba",
    "styles.css": "fd6fe2d6dfb05ef78f56006150af5f6ec499110813bbf65f62928d6ff684ff43",
    "app.js": "420e47015e9dd5fcfb1ef0934381597acbeb313d0375a56a1b3791693a673258",
    "sw.js": "3c54a84f9294aec06a86189e750b3b850e02ea3ad88522f5a43e97e097285c58",
    "aster-compass.png": None,
}
NEW = {
    "index.html": "6a261b921fbd8749b17751f5e3588fd1813c00d476e9aadd235c9ab8efd563ad",
    "styles.css": "94b29a28d37aa935f28b3859cefee81c93fb9fafc5106abf6963a01099e9b87b",
    "app.js": "003e51fe2a4f02ccd0bb930cc72966e4dac1d131c806d512f453f653baca3d33",
    "sw.js": "0ca9eb192d0c000baffb12889c655d3c795bcce38efeaf168eabd580c730c6ed",
    "aster-compass.png": "6b8788ade5bcc3447d93f497a296e55354e15a4dd9a403b22268c907c0f67ddf",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*command: str, check: bool = True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def assert_state(root: Path, expected: Dict[str, Optional[str]]) -> None:
    for name, value in expected.items():
        path = root / name
        if value is None:
            if path.exists():
                raise RuntimeError(f"remote-room-controls-unexpected:{name}")
        elif not path.is_file() or digest(path) != value:
            raise RuntimeError(f"remote-room-controls-drift:{name}")


def atomic_copy(source: Path, destination: Path) -> None:
    stat = destination.stat() if destination.exists() else None
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(descriptor)
    temporary_path = Path(temporary)
    try:
        shutil.copyfile(source, temporary_path)
        if stat is not None:
            os.chown(temporary_path, stat.st_uid, stat.st_gid)
            os.chmod(temporary_path, stat.st_mode & 0o777)
        else:
            os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, destination)
    finally:
        temporary_path.unlink(missing_ok=True)


def checkpoint() -> None:
    if CHECKPOINT.exists():
        raise RuntimeError("remote-room-controls-checkpoint-exists")
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    for name, value in OLD.items():
        if value is not None:
            shutil.copy2(STATIC_TARGET / name, CHECKPOINT / name)
    shutil.copy2(MODULE_TARGET, CHECKPOINT / "aster_remote.py")
    (CHECKPOINT / "manifest.json").write_text(json.dumps({"schema": 1, "host": HOST, "files": OLD, "module": OLD_MODULE}, sort_keys=True) + "\n")
    os.chmod(CHECKPOINT / "manifest.json", 0o600)
    assert_state(CHECKPOINT, OLD)
    if digest(CHECKPOINT / "aster_remote.py") != OLD_MODULE:
        raise RuntimeError("remote-room-controls-module-checkpoint-drift")


def route_hash(path: str) -> str:
    with urllib.request.urlopen("http://192.168.70.10:9120" + path, timeout=4) as response:
        if response.status != 200:
            raise RuntimeError(f"remote-room-controls-route:{path}")
        return hashlib.sha256(response.read()).hexdigest()


def validate(expected: Dict[str, Optional[str]]) -> None:
    assert_state(STATIC_TARGET, expected)
    routes = {
        "/remote/": "index.html", "/remote/styles.css": "styles.css",
        "/remote/app.js": "app.js", "/remote/sw.js": "sw.js",
    }
    if expected["aster-compass.png"] is not None:
        routes["/remote/aster-compass.png"] = "aster-compass.png"
    for route, name in routes.items():
        if route_hash(route) != expected[name]:
            raise RuntimeError(f"remote-room-controls-http-drift:{name}")
    try:
        urllib.request.urlopen("http://192.168.70.10:9120/v1/remote/session", timeout=4)
    except urllib.error.HTTPError as error:
        if error.code == 401:
            return
    raise RuntimeError("remote-room-controls-auth-regression")


def wait_ready() -> None:
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://192.168.70.10:9120/health", timeout=2) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.25)
    raise RuntimeError("remote-room-controls-service-not-ready")


def restore() -> None:
    assert_state(CHECKPOINT, OLD)
    for name, value in OLD.items():
        if value is None:
            (STATIC_TARGET / name).unlink(missing_ok=True)
        else:
            atomic_copy(CHECKPOINT / name, STATIC_TARGET / name)
    atomic_copy(CHECKPOINT / "aster_remote.py", MODULE_TARGET)


def install(source: Path) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-room-controls-wrong-target")
    assert_state(source, NEW)
    module_source = source.parents[1] / "aster_remote.py"
    if not module_source.is_file() or digest(module_source) != NEW_MODULE:
        raise RuntimeError("remote-room-controls-module-source-drift")
    assert_state(STATIC_TARGET, OLD)
    if digest(MODULE_TARGET) != OLD_MODULE:
        raise RuntimeError("remote-room-controls-module-live-drift")
    checkpoint()
    run("systemctl", "stop", "aster-agent")
    try:
        for name in NEW:
            atomic_copy(source / name, STATIC_TARGET / name)
        atomic_copy(module_source, MODULE_TARGET)
        run("systemctl", "start", "aster-agent")
        wait_ready()
        if digest(MODULE_TARGET) != NEW_MODULE:
            raise RuntimeError("remote-room-controls-module-install-drift")
        validate(NEW)
    except Exception:
        run("systemctl", "stop", "aster-agent", check=False)
        restore()
        run("systemctl", "start", "aster-agent")
        wait_ready()
        validate(OLD)
        raise
    print(json.dumps({"outcome": "installed", "checkpoint": str(CHECKPOINT), "service_restart": True, "equipment_authority": False}, sort_keys=True))


def rollback() -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-room-controls-wrong-target")
    assert_state(STATIC_TARGET, NEW)
    if digest(MODULE_TARGET) != NEW_MODULE:
        raise RuntimeError("remote-room-controls-module-live-drift")
    run("systemctl", "stop", "aster-agent")
    restore()
    run("systemctl", "start", "aster-agent")
    wait_ready()
    validate(OLD)
    print(json.dumps({"outcome": "rolled-back", "checkpoint": str(CHECKPOINT), "service_restart": True}, sort_keys=True))


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--source", type=Path)
group.add_argument("--rollback", action="store_true")
arguments = parser.parse_args()
rollback() if arguments.rollback else install(arguments.source)
