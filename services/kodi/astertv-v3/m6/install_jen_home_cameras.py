#!/usr/bin/env python3
"""Checkpoint/install/rollback Jen's bounded M6 Home/Cameras candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess


HOST = "AsterTV-Jen"
KODI = Path("/storage/.kodi")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m6-jen")
STABLE = Path("/storage/.aster-v3/m6")
SERVICE = Path("/storage/.config/system.d/astertv-v3-m6-jen.service")
TARGETS = {
    "home.xml": KODI / "addons/skin.asterhome/1080i/custom_1112_home.xml",
    "cameras.xml": KODI / "addons/skin.asterhome/1080i/custom_1134_cameras.xml",
    "camera-view.py": KODI / "addons/script.asterruntime/aster-camera2/view.py",
    "profile-addon.xml": KODI / "addons/script.asterprofiles.v3lab/addon.xml",
    "registry.py": KODI / "addons/script.asterprofiles.v3lab/registry.py",
    "access_policy.py": KODI / "addons/script.asterprofiles.v3lab/access_policy.py",
    "authority.py": KODI / "addons/script.asterprofiles.v3lab/authority.py",
    "identity_resolver.py": KODI / "addons/script.asterprofiles.v3lab/identity_resolver.py",
    "astertv-voice.py": KODI / "addons/script.astertv.voice/default.py",
    "profiles.json": KODI / "userdata/addon_data/script.asterprofiles.v3lab/profiles.json",
    "profiles.previous.json": KODI / "userdata/addon_data/script.asterprofiles.v3lab/profiles.json.previous",
    "display-identity.json": Path("/storage/.aster-home/display-identity.json"),
}
PREDECESSORS = {
    "home.xml": "ec3cae3a5bc7f2c687b2cd3d997947d3f2f76e195fb4b61243b1941db677266f",
    "camera-view.py": "5cf2ffc7b74df3dcdd4651c4f1984b1aed233404146551945c4cd7e40982d1df",
    "profile-addon.xml": "94d57ce593d5b74add30554452b3a43df349291378897c60e359c4b647256b36",
    "registry.py": "4faaef3f7d5c17531016984406b3c88d18f61c6673fd82cf6e4300f0d5b03134",
    "access_policy.py": "1e25d85e1b5b3fb5843eec0cd61ad2f697aeda47c7ee310d9dce1678252dc2af",
    "authority.py": "08e2d206d5f6ea1cbc7afeacb4d3416e022b6536dab8f0304fc995a80bd13406",
    "identity_resolver.py": "46e52ee6fd089c43131eb342854657df2afb9cbbbb9492e9b57dfd192a0748e9",
    "astertv-voice.py": "e72198e613ac43a27505be032d2d3e2a3d8d3fc238ef5a0ba72fc943d5a76a93",
}


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rpc(method):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        response = json.loads(connection.recv(65536))
    if "error" in response:
        raise RuntimeError("rpc:" + method)
    return response.get("result")


def preflight():
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    for name, expected in PREDECESSORS.items():
        if sha(TARGETS[name]) != expected:
            raise RuntimeError("predecessor-drift:" + name)
    if TARGETS["cameras.xml"].exists() or TARGETS["display-identity.json"].exists():
        raise RuntimeError("new-target-already-present")


def checkpoint():
    if CHECKPOINT.exists():
        raise RuntimeError("checkpoint-exists")
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    rows = []
    for name, target in TARGETS.items():
        present = target.exists()
        if present:
            destination = CHECKPOINT / name
            shutil.copy2(target, destination)
            rows.append({"name": name, "present": True, "sha256": sha(destination)})
        else:
            rows.append({"name": name, "present": False})
    report = {"schema": 1, "host": HOST, "targets": rows,
              "service_present": SERVICE.exists(), "stable_present": STABLE.exists()}
    path = CHECKPOINT / "checkpoint.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(path, 0o600)


def install(source):
    preflight(); checkpoint()
    STABLE.mkdir(parents=True, mode=0o700)
    sources = {
        "Home.base.xml": source / "fixtures/custom_1112_home.predecessor.xml",
        "custom_1134_cameras.xml": source / "addon/skin/custom_1134_cameras.xml",
        "camera-view.py": source / "addon/aster-camera2/view.py",
        "home_overlay.py": source / "home_overlay.py",
        "apply_jen_home_cameras.py": source / "apply_jen_home_cameras.py",
        "install_jen_home_cameras.py": source / "install_jen_home_cameras.py",
        "profile-addon.xml": source.parent / "accounts/addon/script.asterprofiles.v3lab/addon.xml",
        "registry.py": source.parent / "accounts/registry.py",
        "access_policy.py": source.parent / "accounts/access_policy.py",
        "authority.py": source.parent / "accounts/authority.py",
        "identity_resolver.py": source.parent / "accounts/identity_resolver.py",
        "astertv-voice.py": source.parent / "aster_client/addon/script.astertv.voice/default.py",
    }
    for name, path in sources.items():
        shutil.copy2(path, STABLE / name); os.chmod(STABLE / name, 0o600)
    marker = {"authority": "ha-home-dashboard-v4", "kind": "astertv-home-display", "schema": 1}
    (STABLE / "display-identity.json").write_text(json.dumps(marker, sort_keys=True) + "\n")
    os.chmod(STABLE / "display-identity.json", 0o600)
    SERVICE.write_text(
        "[Unit]\nDescription=Apply AsterTV v3 M6 Home and Cameras on Jen\n"
        "After=astertv-v3-m5p-jen.service\nBefore=kodi.service\n"
        "[Service]\nType=oneshot\n"
        "ExecStart=/usr/bin/python3 /storage/.aster-v3/m6/apply_jen_home_cameras.py\n"
        "[Install]\nWantedBy=kodi.service\n"
    )
    run("systemctl", "daemon-reload")
    run("systemctl", "stop", "kodi")
    try:
        run("python3", str(STABLE / "apply_jen_home_cameras.py"))
        run("systemctl", "enable", "astertv-v3-m6-jen.service")
    finally:
        run("systemctl", "start", "kodi")
    print(json.dumps({"outcome": "installed", "host": HOST,
                      "checkpoint": str(CHECKPOINT)}, sort_keys=True))


def rollback():
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    report = json.loads((CHECKPOINT / "checkpoint.json").read_text())
    if report.get("host") != HOST:
        raise RuntimeError("checkpoint-host-mismatch")
    run("systemctl", "stop", "kodi")
    try:
        for row in report["targets"]:
            target = TARGETS[row["name"]]
            if row["present"]:
                source = CHECKPOINT / row["name"]
                if sha(source) != row["sha256"]:
                    raise RuntimeError("checkpoint-drift:" + row["name"])
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            elif target.exists():
                target.unlink()
        if not report["service_present"] and SERVICE.exists():
            SERVICE.unlink()
        if not report["stable_present"] and STABLE.exists():
            shutil.rmtree(STABLE)
        run("systemctl", "daemon-reload")
    finally:
        run("systemctl", "start", "kodi")
    for name, expected in PREDECESSORS.items():
        if sha(TARGETS[name]) != expected:
            raise RuntimeError("rollback-drift:" + name)
    print(json.dumps({"outcome": "rolled-back", "host": HOST}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=Path)
    group.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    rollback() if args.rollback else install(args.source)


if __name__ == "__main__":
    main()
