#!/usr/bin/env python3
"""Checkpoint and install the approved Aster Remote launcher assets."""

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
import urllib.error
import urllib.request


HOST = "hermesagent"
GATEWAY = Path("/opt/aster-agent/aster_remote.py")
TARGET = Path("/opt/aster-agent/static/remote")
CHECKPOINT = Path("/var/lib/aster/checkpoints/astertv-v3-remote-brand-assets-20261106")
STATIC_FILES = (
    "index.html", "sw.js", "manifest.webmanifest",
    "astertv-remote-180.png", "astertv-remote-512.png",
)
OLD = {
    "aster_remote.py": "f2780775df560903ecf6a0b4efe224343f327914bd680fe8fdd4abb24484e983",
    "index.html": "21df9781d38e31423be9ac9b78508fe618ff9e1a6bdb877eec07818ab38e00c6",
    "sw.js": "9be36dd12a332cf22c71c3364479b23623b2a10abb07b8be0a5f8c27bc0f2bc8",
    "manifest.webmanifest": "1f60d65e19b010afcf11e58b1184341f39e98a59f768419c28a41832e7a5795b",
    "astertv-remote-180.png": None,
    "astertv-remote-512.png": None,
}
NEW = {
    "aster_remote.py": "39d6239df804a86a74f187f6c24eb185f6fe9bd2e5a56fdab4bb20c5fcba1231",
    "index.html": "54d11f133fcfd341487dcbbe190479b13451458a7c19041075c35db257949df5",
    "sw.js": "b72b204d8220cbf5f122aac9e8d384a91bb10c8613cd5b54a46d774fd74ebfa7",
    "manifest.webmanifest": "2cef646afa075a39e4f1316ae5e9d91b9f644a14b3d68b14cf48dc78077b5e8d",
    "astertv-remote-180.png": "36eb73e019be374fbf4cb2fdf2e16de14b30e0dc470cbc5b19fae63bc4ba8379",
    "astertv-remote-512.png": "07880f3fb4e791b6383cabfe3c77a5218c184e84073c8cb89037e9b9c5a16074",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def live_paths() -> dict[str, Path]:
    return {"aster_remote.py": GATEWAY, **{name: TARGET / name for name in STATIC_FILES}}


def assert_state(expected: dict[str, str | None]) -> None:
    for name, digest in expected.items():
        path = live_paths()[name]
        if digest is None:
            if path.exists():
                raise RuntimeError(f"remote-brand-unexpected:{name}")
        elif not path.is_file() or sha(path.read_bytes()) != digest:
            raise RuntimeError(f"remote-brand-drift:{name}")


def transform_gateway(data: bytes) -> bytes:
    if sha(data) != OLD["aster_remote.py"]:
        raise RuntimeError("remote-brand-gateway-base-drift")
    text = data.decode()
    route = '        self.router.add_api_route("/remote/aster-compass.png", self.asset, methods=["GET"])\n'
    media = '            "aster-compass.png": "image/png",\n'
    if text.count(route) != 1 or text.count(media) != 1:
        raise RuntimeError("remote-brand-gateway-anchor-drift")
    text = text.replace(route, route +
        '        self.router.add_api_route("/remote/astertv-remote-180.png", self.asset, methods=["GET"])\n'
        '        self.router.add_api_route("/remote/astertv-remote-512.png", self.asset, methods=["GET"])\n')
    text = text.replace(media, media +
        '            "astertv-remote-180.png": "image/png",\n'
        '            "astertv-remote-512.png": "image/png",\n')
    candidate = text.encode()
    if sha(candidate) != NEW["aster_remote.py"]:
        raise RuntimeError("remote-brand-gateway-candidate-drift")
    return candidate


def atomic_write(path: Path, data: bytes, uid: int, gid: int, mode: int = 0o644) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chown(temporary, uid, gid); os.chmod(temporary, mode); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def checkpoint() -> None:
    if CHECKPOINT.exists():
        manifest = CHECKPOINT / "manifest.json"
        saved = CHECKPOINT / "aster_remote.py"
        if (not manifest.is_file() or not saved.is_file()
                or sha(saved.read_bytes()) != OLD["aster_remote.py"]):
            raise RuntimeError("remote-brand-checkpoint-drift")
        record = json.loads(manifest.read_text())
        if record.get("host") != HOST or record.get("before") != OLD or record.get("after") != NEW:
            raise RuntimeError("remote-brand-checkpoint-drift")
        return
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    for name, path in live_paths().items():
        if path.is_file():
            shutil.copy2(path, CHECKPOINT / name)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "schema": 1, "host": HOST, "before": OLD, "after": NEW,
        "source_svg_sha256": "7effb1ffe3ba828de63059235c976f26e0d7fb869e0856d0fb52cea86a775ada",
    }, indent=2, sort_keys=True) + "\n")
    os.chmod(CHECKPOINT / "manifest.json", 0o600)


def validate() -> None:
    assert_state(NEW)
    if subprocess.run(["systemctl", "is-active", "--quiet", "aster-agent.service"]).returncode:
        raise RuntimeError("remote-brand-service-inactive")
    for name in STATIC_FILES:
        route = "" if name == "index.html" else name
        try:
            with urllib.request.urlopen("http://192.168.70.10:9120/remote/" + route, timeout=5) as response:
                if response.status != 200 or sha(response.read()) != NEW[name]:
                    raise RuntimeError(f"remote-brand-http-drift:{name}")
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"remote-brand-http-status:{name}:{error.code}") from error
    request = urllib.request.Request("http://192.168.70.10:9120/v1/remote/session")
    try:
        urllib.request.urlopen(request, timeout=4)
    except urllib.error.HTTPError as error:
        if error.code == 403:
            return
    raise RuntimeError("remote-brand-auth-regression")


def restore() -> None:
    gateway_stat = GATEWAY.stat()
    for name, path in live_paths().items():
        saved = CHECKPOINT / name
        if saved.is_file():
            stat = path.stat() if path.exists() else gateway_stat
            atomic_write(path, saved.read_bytes(), stat.st_uid, stat.st_gid, stat.st_mode & 0o777)
        elif path.exists():
            path.unlink()
    subprocess.run(["systemctl", "restart", "aster-agent.service"], check=True, timeout=45)
    assert_state(OLD)


def install(source: Path) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-brand-wrong-target")
    assert_state(OLD)
    for name in STATIC_FILES:
        candidate = source / name
        if not candidate.is_file() or sha(candidate.read_bytes()) != NEW[name]:
            raise RuntimeError(f"remote-brand-source-drift:{name}")
    gateway = transform_gateway(GATEWAY.read_bytes())
    checkpoint()
    try:
        gateway_stat = GATEWAY.stat()
        atomic_write(GATEWAY, gateway, gateway_stat.st_uid, gateway_stat.st_gid, gateway_stat.st_mode & 0o777)
        for name in STATIC_FILES:
            path = TARGET / name
            stat = path.stat() if path.exists() else (TARGET / "manifest.webmanifest").stat()
            atomic_write(path, (source / name).read_bytes(), stat.st_uid, stat.st_gid, 0o644)
        subprocess.run(["systemctl", "restart", "aster-agent.service"], check=True, timeout=45)
        for _ in range(20):
            try:
                validate(); break
            except (OSError, urllib.error.URLError, RuntimeError):
                time.sleep(0.5)
        else:
            validate()
    except Exception:
        restore(); raise
    print(json.dumps({"outcome": "installed", "checkpoint": str(CHECKPOINT), "files": NEW}, sort_keys=True))


def rollback() -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("remote-brand-wrong-target")
    assert_state(NEW); restore()
    print(json.dumps({"outcome": "rolled-back", "checkpoint": str(CHECKPOINT)}, sort_keys=True))


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--source", type=Path)
group.add_argument("--rollback", action="store_true")
arguments = parser.parse_args()
rollback() if arguments.rollback else install(arguments.source)

