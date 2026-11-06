#!/usr/bin/env python3
"""Checkpoint and install the approved R5 AsterTV startup splash."""

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


ALLOWED_HOSTS = {"AsterTV-Jen", "AsterTV-Bedroom", "AsterTV-Family"}
TARGET = Path("/storage/.kodi/media/Splash.png")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-r5-splash-20261106")
OLD_SHA256 = "912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce"
NEW_SHA256 = "3658771b8ab771591839713cd497cc79a5a781d67463145fe2f23c3d541d4626"
SOURCE_SVG_SHA256 = "747aab438334afc9b1e2a0dafa8608bd8b8d4aa5ed29af5697f22972b714d2e8"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kodi_rpc(method: str) -> dict:
    request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method}).encode() + b"\n"
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as stream:
        stream.sendall(request)
        response = stream.recv(65536)
    return json.loads(response.decode())


def assert_idle() -> None:
    response = kodi_rpc("Player.GetActivePlayers")
    if response.get("result") != []:
        raise RuntimeError("splash-install-playback-active")


def atomic_copy(source: Path, target: Path) -> None:
    stat = target.stat()
    descriptor, temporary = tempfile.mkstemp(prefix=".Splash.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(source.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.chown(temporary, stat.st_uid, stat.st_gid)
        os.chmod(temporary, stat.st_mode & 0o777)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def wait_for_kodi() -> None:
    for _ in range(30):
        if subprocess.run(("systemctl", "is-active", "--quiet", "kodi"), check=False).returncode == 0:
            try:
                if kodi_rpc("Player.GetActivePlayers").get("result") == []:
                    return
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        time.sleep(1)
    raise RuntimeError("splash-install-kodi-not-ready")


def checkpoint(host: str) -> None:
    if CHECKPOINT.exists():
        raise RuntimeError("splash-install-checkpoint-exists")
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    shutil.copy2(TARGET, CHECKPOINT / "Splash.png")
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "schema": 1,
        "host": host,
        "target": str(TARGET),
        "before_sha256": OLD_SHA256,
        "after_sha256": NEW_SHA256,
        "source_svg_sha256": SOURCE_SVG_SHA256,
    }, indent=2, sort_keys=True) + "\n")
    os.chmod(CHECKPOINT / "manifest.json", 0o600)


def install(source: Path) -> dict:
    host = socket.gethostname()
    if os.getuid() != 0 or host not in ALLOWED_HOSTS:
        raise RuntimeError("splash-install-wrong-target")
    if not source.is_file() or sha256(source) != NEW_SHA256:
        raise RuntimeError("splash-install-source-drift")
    if not TARGET.is_file() or sha256(TARGET) != OLD_SHA256:
        raise RuntimeError("splash-install-baseline-drift")
    assert_idle()
    checkpoint(host)
    stopped = False
    try:
        subprocess.run(("systemctl", "stop", "kodi"), check=True, timeout=45)
        stopped = True
        atomic_copy(source, TARGET)
        subprocess.run(("systemctl", "start", "kodi"), check=True, timeout=45)
        stopped = False
        wait_for_kodi()
        if sha256(TARGET) != NEW_SHA256:
            raise RuntimeError("splash-install-target-drift")
    except Exception:
        if not stopped:
            subprocess.run(("systemctl", "stop", "kodi"), check=False, timeout=45)
        atomic_copy(CHECKPOINT / "Splash.png", TARGET)
        subprocess.run(("systemctl", "start", "kodi"), check=False, timeout=45)
        raise
    result = {"outcome": "installed", "host": host, "checkpoint": str(CHECKPOINT),
              "splash_sha256": NEW_SHA256}
    print(json.dumps(result, sort_keys=True))
    return result


def rollback() -> dict:
    host = socket.gethostname()
    saved = CHECKPOINT / "Splash.png"
    if os.getuid() != 0 or host not in ALLOWED_HOSTS or not saved.is_file():
        raise RuntimeError("splash-rollback-unavailable")
    assert_idle()
    if sha256(TARGET) != NEW_SHA256 or sha256(saved) != OLD_SHA256:
        raise RuntimeError("splash-rollback-state-drift")
    subprocess.run(("systemctl", "stop", "kodi"), check=True, timeout=45)
    atomic_copy(saved, TARGET)
    subprocess.run(("systemctl", "start", "kodi"), check=True, timeout=45)
    wait_for_kodi()
    result = {"outcome": "rolled-back", "host": host, "splash_sha256": OLD_SHA256}
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=Path)
    group.add_argument("--rollback", action="store_true")
    arguments = parser.parse_args()
    rollback() if arguments.rollback else install(arguments.source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
