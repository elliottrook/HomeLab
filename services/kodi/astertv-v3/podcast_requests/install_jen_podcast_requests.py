#!/usr/bin/env python3
"""Checkpoint and install or roll back Jen's M5 podcast request surface."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

from apply_jen_podcast_requests import HOST, INCLUDES, PODCASTS, ADDON


CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m5p-jen")
STABLE = Path("/storage/.aster-v3/m5p")
SERVICE = Path("/storage/.config/system.d/astertv-v3-m5p-jen.service")
CONFIG = Path("/storage/.kodi/userdata/addon_data/script.astertv.podcast.requests/client.json")
BASE_INCLUDES = "0ba7ab639f0819fb057389c69652fd134e8330f08584bfe575c0a3874d58be4d"
BASE_PODCASTS = "70bb81dc58d3373ee434ca70b17b81c8823a41f27d51829891c8eba2f7ca7ee6"


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc(method: str):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        reply = json.loads(connection.recv(65536))
    if "error" in reply:
        raise RuntimeError("rpc:" + method)
    return reply.get("result")


def wait_rpc(method: str, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    last = None
    for _attempt in range(60):
        try:
            with socket.create_connection(("127.0.0.1", 9090), timeout=2) as connection:
                connection.sendall((json.dumps(request) + "\r\n").encode())
                response = json.loads(connection.recv(65536))
            if "error" not in response:
                return response.get("result")
            last = response["error"]
        except (OSError, json.JSONDecodeError) as error:
            last = error
        time.sleep(1)
    raise RuntimeError("kodi-rpc-timeout:" + str(last))


def checkpoint() -> None:
    if CHECKPOINT.exists():
        raise RuntimeError("checkpoint-exists")
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    shutil.copy2(INCLUDES, CHECKPOINT / "IncludesBooks.xml")
    shutil.copy2(PODCASTS, CHECKPOINT / "custom_1120_podcasts.xml")
    manifest = {"schema": 1, "host": HOST, "includes_sha256": sha256(INCLUDES),
                "podcasts_sha256": sha256(PODCASTS), "addon_present": ADDON.exists(),
                "service_present": SERVICE.exists(), "stable_present": STABLE.exists()}
    target = CHECKPOINT / "checkpoint.json"
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.chmod(target, 0o600)


def install(source: Path) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    if sha256(INCLUDES) != BASE_INCLUDES or sha256(PODCASTS) != BASE_PODCASTS:
        raise RuntimeError("skin-base-drift")
    if ADDON.exists() or not CONFIG.is_file() or CONFIG.is_symlink() or CONFIG.stat().st_mode & 0o077:
        raise RuntimeError("addon-or-config-state")
    checkpoint()
    STABLE.mkdir(parents=True, mode=0o700)
    shutil.copy2(INCLUDES, STABLE / "IncludesBooks.base.xml")
    shutil.copy2(PODCASTS, STABLE / "custom_1120_podcasts.base.xml")
    shutil.copy2(source / "apply_jen_podcast_requests.py", STABLE / "apply_jen_podcast_requests.py")
    shutil.copytree(source / "addon/script.astertv.podcast.requests",
                    STABLE / "script.astertv.podcast.requests")
    for path in STABLE.rglob("*"):
        if path.is_file():
            os.chmod(path, 0o600)
    SERVICE.write_text(
        "[Unit]\nDescription=Apply AsterTV v3 podcast request UI on Jen\n"
        "After=astertv-v3-m5n-jen.service\nBefore=kodi.service\n"
        "[Service]\nType=oneshot\n"
        "ExecStart=/usr/bin/python3 /storage/.aster-v3/m5p/apply_jen_podcast_requests.py\n"
        "[Install]\nWantedBy=kodi.service\n"
    )
    run("systemctl", "daemon-reload")
    run("systemctl", "stop", "kodi")
    try:
        run("python3", str(STABLE / "apply_jen_podcast_requests.py"))
        run("systemctl", "enable", "astertv-v3-m5p-jen.service")
    finally:
        run("systemctl", "start", "kodi")
    wait_rpc("Addons.SetAddonEnabled", {
        "addonid": "script.astertv.podcast.requests", "enabled": True})
    print(json.dumps({"outcome": "installed", "host": HOST,
                      "checkpoint": str(CHECKPOINT)}, sort_keys=True))


def rollback() -> None:
    if socket.gethostname() != HOST or rpc("Player.GetActivePlayers"):
        raise RuntimeError("rollback-boundary")
    manifest = json.loads((CHECKPOINT / "checkpoint.json").read_text())
    if manifest.get("host") != HOST or manifest.get("addon_present"):
        raise RuntimeError("checkpoint-mismatch")
    run("systemctl", "stop", "kodi")
    try:
        shutil.copy2(CHECKPOINT / "IncludesBooks.xml", INCLUDES)
        shutil.copy2(CHECKPOINT / "custom_1120_podcasts.xml", PODCASTS)
        if ADDON.exists():
            shutil.rmtree(ADDON)
        if not manifest["service_present"] and SERVICE.exists():
            SERVICE.unlink()
        if not manifest["stable_present"] and STABLE.exists():
            shutil.rmtree(STABLE)
        run("systemctl", "daemon-reload")
    finally:
        run("systemctl", "start", "kodi")
    if sha256(INCLUDES) != manifest["includes_sha256"] or sha256(PODCASTS) != manifest["podcasts_sha256"]:
        raise RuntimeError("rollback-hash")
    print(json.dumps({"outcome": "rolled-back", "host": HOST}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source", type=Path)
    mode.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    rollback() if args.rollback else install(args.source)


if __name__ == "__main__":
    main()
