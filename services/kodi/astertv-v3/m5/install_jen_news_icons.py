#!/usr/bin/env python3
"""Checkpoint, install or roll back the bounded Jen M5 News icon overlay."""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path


HOST = "AsterTV-Jen"
NEWS = Path("/storage/.kodi/addons/skin.asterhome/1080i/custom_1111_digest.xml")
COMPASS = Path("/storage/.kodi/addons/skin.asterhome/media/aster-compass-128.png")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m5n-jen")
STABLE = Path("/storage/.aster-v3/m5n")
SERVICE = Path("/storage/.config/system.d/astertv-v3-m5n-jen.service")
BASE_SHA256 = "960645920dc25fd709c0310b178057afaae16fa5260404110b03fda98669cd77"


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rpc(method):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        reply = json.loads(connection.recv(65536))
    if "error" in reply:
        raise RuntimeError("rpc:" + method)
    return reply.get("result")


def load(path):
    spec = importlib.util.spec_from_file_location("m5n_apply", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checkpoint():
    if CHECKPOINT.exists():
        manifest = json.loads((CHECKPOINT / "checkpoint.json").read_text())
        if manifest.get("host") != HOST or manifest.get("news_sha256") != BASE_SHA256:
            raise RuntimeError("checkpoint-mismatch")
        return False
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    shutil.copy2(NEWS, CHECKPOINT / "custom_1111_digest.xml")
    manifest = {
        "schema": 1,
        "host": HOST,
        "news_sha256": sha256(NEWS),
        "service_present": SERVICE.exists(),
        "stable_present": STABLE.exists(),
    }
    path = CHECKPOINT / "checkpoint.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.chmod(path, 0o600)
    return True


def install(source):
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    if sha256(NEWS) != BASE_SHA256:
        raise RuntimeError("news-base-drift")
    if not COMPASS.is_file():
        raise RuntimeError("compass-missing")
    checkpoint()
    STABLE.mkdir(parents=True, mode=0o700, exist_ok=True)
    shutil.copy2(NEWS, STABLE / "News.base.xml")
    shutil.copy2(source / "apply_jen_news_icons.py", STABLE / "apply_jen_news_icons.py")
    shutil.copy2(source / "install_jen_news_icons.py", STABLE / "install_jen_news_icons.py")
    for path in STABLE.iterdir():
        os.chmod(path, 0o600)
    SERVICE.write_text(
        "[Unit]\nDescription=Apply AsterTV v3 M5 News icons on Jen\n"
        "After=astertv-v3-m4y-jen.service\nBefore=kodi.service\n"
        "[Service]\nType=oneshot\n"
        "ExecStart=/usr/bin/python3 /storage/.aster-v3/m5n/apply_jen_news_icons.py\n"
        "[Install]\nWantedBy=kodi.service\n"
    )
    run("systemctl", "daemon-reload")
    run("systemctl", "stop", "kodi")
    try:
        run("python3", str(STABLE / "apply_jen_news_icons.py"))
        run("systemctl", "enable", "astertv-v3-m5n-jen.service")
    finally:
        run("systemctl", "start", "kodi")
    print(json.dumps({"outcome": "installed", "host": HOST}, sort_keys=True))


def rollback():
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    manifest = json.loads((CHECKPOINT / "checkpoint.json").read_text())
    if manifest.get("host") != HOST:
        raise RuntimeError("checkpoint-host-mismatch")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    run("systemctl", "stop", "kodi")
    try:
        shutil.copy2(CHECKPOINT / "custom_1111_digest.xml", NEWS)
        if not manifest.get("service_present") and SERVICE.exists():
            SERVICE.unlink()
        if not manifest.get("stable_present") and STABLE.exists():
            shutil.rmtree(STABLE)
        run("systemctl", "daemon-reload")
    finally:
        run("systemctl", "start", "kodi")
    if sha256(NEWS) != manifest["news_sha256"]:
        raise RuntimeError("rollback-hash-mismatch")
    print(json.dumps({"outcome": "rolled-back", "host": HOST}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source", type=Path)
    mode.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    rollback() if args.rollback else install(args.source)


if __name__ == "__main__":
    main()
