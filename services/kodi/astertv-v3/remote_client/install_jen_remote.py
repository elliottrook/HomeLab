#!/usr/bin/env python3
"""Checkpoint/install/rollback Jen's outbound-only Aster Remote client."""

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


HOST = "AsterTV-Jen"
KODI = Path("/storage/.kodi")
ADDON = KODI / "addons/service.asterremote"
DATABASE = KODI / "userdata/Database/Addons33.db"
KEY = Path("/storage/.aster-private/asterremote-client.key")
INPUT_KEY = Path("/run/asterremote-client.key")
STABLE = Path("/storage/.aster-v3/m8")
SERVICE = Path("/storage/.config/system.d/astertv-v3-m8-jen.service")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m8-jen")
TARGETS = {"addon": ADDON, "database": DATABASE, "key": KEY,
           "stable": STABLE, "service": SERVICE}


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_sha(path):
    value = hashlib.sha256()
    for item in sorted(row for row in Path(path).rglob("*") if row.is_file()):
        value.update(str(item.relative_to(path)).encode() + b"\0")
        value.update(item.read_bytes())
    return value.hexdigest()


def path_sha(path):
    return tree_sha(path) if Path(path).is_dir() else sha(path)


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        result = json.loads(connection.recv(65536))
    if "error" in result:
        raise RuntimeError("kodi-rpc:" + method)
    return result.get("result")


def private_key():
    if not INPUT_KEY.is_file() or INPUT_KEY.stat().st_mode & 0o077:
        raise RuntimeError("private-input-key-required")
    value = INPUT_KEY.read_text().strip()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise RuntimeError("invalid-input-key")
    return value


def preflight(source):
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    if not DATABASE.is_file() or not (source / "addon/service.asterremote/addon.xml").is_file():
        raise RuntimeError("source-or-database-missing")
    if not (source / "apply_remote_client.py").is_file():
        raise RuntimeError("apply-source-missing")
    if not CHECKPOINT.exists() and any(path.exists() for name, path in TARGETS.items()
                                       if name != "database"):
        raise RuntimeError("new-target-already-present")
    return private_key()


def copy_path(source, destination):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def remove_path(path):
    path = Path(path)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def checkpoint():
    if CHECKPOINT.exists():
        report = json.loads((CHECKPOINT / "checkpoint.json").read_text())
        if report.get("host") != HOST or set(row["name"] for row in report["targets"]) != set(TARGETS):
            raise RuntimeError("checkpoint-mismatch")
        for row in report["targets"]:
            current = TARGETS[row["name"]]
            if row["present"] != current.exists():
                raise RuntimeError("rollback-state-not-restored:" + row["name"])
            if row["present"] and path_sha(current) != row["sha256"]:
                raise RuntimeError("rollback-state-drift:" + row["name"])
        return
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    rows = []
    for name, target in TARGETS.items():
        row = {"name": name, "path": str(target), "present": target.exists()}
        if target.exists():
            saved = CHECKPOINT / "files" / name
            copy_path(target, saved)
            row.update({"sha256": path_sha(saved), "directory": saved.is_dir()})
        rows.append(row)
    report = {"schema": 1, "kind": "astertv-v3-m8-jen-client",
              "host": HOST, "targets": rows, "service_enabled": False}
    metadata = CHECKPOINT / "checkpoint.json"
    metadata.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(metadata, 0o600)


def restore():
    report = json.loads((CHECKPOINT / "checkpoint.json").read_text())
    if report.get("host") != HOST:
        raise RuntimeError("checkpoint-host")
    run("systemctl", "disable", "astertv-v3-m8-jen.service", check=False)
    for row in report["targets"]:
        target = TARGETS[row["name"]]
        if row["present"]:
            saved = CHECKPOINT / "files" / row["name"]
            if path_sha(saved) != row["sha256"]:
                raise RuntimeError("checkpoint-drift:" + row["name"])
            copy_path(saved, target)
        else:
            remove_path(target)


def wait_kodi():
    for _ in range(50):
        try:
            rpc("JSONRPC.Ping")
            return
        except (OSError, RuntimeError, ValueError):
            time.sleep(0.2)
    raise RuntimeError("kodi-not-ready")


def install(source):
    key = preflight(source)
    run("systemctl", "stop", "kodi")
    installed = False
    try:
        checkpoint()
        STABLE.mkdir(parents=True, mode=0o700)
        copy_path(source / "addon/service.asterremote", STABLE / "service.asterremote")
        shutil.copy2(source / "apply_remote_client.py", STABLE / "apply_remote_client.py")
        os.chmod(STABLE / "apply_remote_client.py", 0o700)
        manifest = {"schema": 1, "addon_sha256": tree_sha(STABLE / "service.asterremote")}
        (STABLE / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
        os.chmod(STABLE / "manifest.json", 0o600)
        KEY.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        KEY.write_text(key + "\n"); os.chmod(KEY, 0o600)
        SERVICE.write_text(
            "[Unit]\nDescription=Apply Aster Remote client on Jen\n"
            "After=astertv-v3-m6-jen.service\nBefore=kodi.service\n"
            "[Service]\nType=oneshot\n"
            "ExecStart=/usr/bin/python3 /storage/.aster-v3/m8/apply_remote_client.py\n"
            "[Install]\nWantedBy=kodi.service\n"
        )
        run("systemctl", "daemon-reload")
        run("python3", str(STABLE / "apply_remote_client.py"))
        run("systemctl", "enable", "astertv-v3-m8-jen.service")
        run("systemctl", "start", "kodi")
        wait_kodi()
        rpc("Addons.SetAddonEnabled", {"addonid": "service.asterremote", "enabled": True})
        detail = rpc("Addons.GetAddonDetails", {
            "addonid": "service.asterremote", "properties": ["enabled"]})
        if detail.get("addon", {}).get("enabled") is not True:
            raise RuntimeError("remote-addon-not-enabled")
        installed = True
    except Exception:
        run("systemctl", "stop", "kodi", check=False)
        restore()
        run("systemctl", "daemon-reload")
        raise
    finally:
        INPUT_KEY.unlink(missing_ok=True)
        if not installed:
            run("systemctl", "start", "kodi")
    print(json.dumps({"outcome": "installed", "host": HOST,
                      "checkpoint": str(CHECKPOINT), "credential_output": False}, sort_keys=True))


def rollback():
    if socket.gethostname() != HOST or os.getuid() != 0 or rpc("Player.GetActivePlayers"):
        raise RuntimeError("rollback-boundary")
    run("systemctl", "stop", "kodi")
    try:
        restore()
        run("systemctl", "daemon-reload")
    finally:
        run("systemctl", "start", "kodi")
    wait_kodi()
    print(json.dumps({"outcome": "rolled-back", "host": HOST,
                      "checkpoint": str(CHECKPOINT)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("install"); add.add_argument("--source", type=Path, required=True)
    sub.add_parser("rollback")
    args = parser.parse_args()
    install(args.source) if args.action == "install" else rollback()


if __name__ == "__main__":
    main()
