#!/usr/bin/env python3
"""Checkpoint and install/rollback the Jen-only AsterTV client candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
from pathlib import Path


EXPECTED_HOST = "AsterTV-Jen"
KODI = Path("/storage/.kodi")
ADDON = KODI / "addons/script.astertv.voice"
PROFILE_DEFAULT = KODI / "addons/script.asterprofiles.v3lab/default.py"
PROFILE_ADDON = PROFILE_DEFAULT.parent
PROFILE_STATE = KODI / "userdata/addon_data/script.asterprofiles.v3lab/profiles.json"
PROFILE_MODULES = ("default.py", "registry.py", "access_policy.py", "authority.py",
                   "identity_resolver.py")
KEY = Path("/storage/.aster-private/astertv-broker.key")
GUARD = Path("/storage/.aster-release/release_guard.py")
CHECKPOINT_ROOT = Path("/storage/.aster-checkpoints")


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def rpc(method, params=None):
    request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method}) + "\r\n"
    if params is not None:
        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                              "params": params}) + "\r\n"
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall(request.encode())
        payload = connection.recv(65536)
    result = json.loads(payload)
    if "error" in result:
        raise RuntimeError("json-rpc-error")
    return result.get("result")


def boundary(source):
    if socket.gethostname() != EXPECTED_HOST:
        raise RuntimeError("wrong-target")
    if not source.is_dir() or (source / "addon.xml").is_symlink():
        raise RuntimeError("invalid-source")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    guard = json.loads(run("python3", str(GUARD), "verify", "--host", EXPECTED_HOST).stdout)
    if guard.get("outcome") != "clean" or guard.get("files") != 528:
        raise RuntimeError("release-guard-not-clean")
    details = KEY.stat()
    if not KEY.is_file() or details.st_mode & 0o077 or len(KEY.read_text().strip()) < 32:
        raise RuntimeError("credential-boundary")
    root = source.parent.parent
    expected = {"default.py": root / "profile-default.py"}
    expected.update({name: root / name for name in PROFILE_MODULES if name != "default.py"})
    if any(not path.is_file() or path.is_symlink() for path in expected.values()):
        raise RuntimeError("profile-source-missing")
    return expected


def checkpoint(identifier):
    destination = CHECKPOINT_ROOT / identifier
    if destination.exists():
        raise RuntimeError("checkpoint-already-exists")
    destination.mkdir(parents=True, mode=0o700)
    rows = []
    for source in tuple(PROFILE_ADDON / name for name in PROFILE_MODULES) + (PROFILE_STATE, KEY):
        if not source.is_file():
            raise RuntimeError("checkpoint-source-missing")
        target = destination / "files" / source.relative_to("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        rows.append({"path": str(source), "sha256": digest(source)})
    if ADDON.exists():
        shutil.copytree(ADDON, destination / "addon")
    report = {"schema": 1, "kind": "astertv-v3-m3-jen-client-checkpoint",
              "host": EXPECTED_HOST, "addon_preexisting": ADDON.exists(), "files": rows}
    manifest = destination / "checkpoint.json"
    manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(manifest, 0o600)
    return destination


def install(source, identifier):
    profile_sources = boundary(source)
    destination = checkpoint(identifier)
    run("systemctl", "stop", "kodi")
    try:
        staging = ADDON.with_name("." + ADDON.name + ".installing")
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(source, staging)
        for path in staging.rglob("*"):
            if path.is_file():
                os.chmod(path, 0o644)
        if ADDON.exists():
            shutil.rmtree(ADDON)
        os.replace(staging, ADDON)
        for name, profile_source in profile_sources.items():
            target = PROFILE_ADDON / name
            profile_staging = target.with_name("." + name + ".installing")
            shutil.copy2(profile_source, profile_staging)
            os.chmod(profile_staging, 0o644)
            os.replace(profile_staging, target)
        import sys
        sys.path.insert(0, str(PROFILE_ADDON))
        from authority import build_registry, load_authority
        from registry import load, store
        from datetime import datetime, timezone
        current, status = load(PROFILE_STATE)
        if status != "valid":
            raise RuntimeError("profile-state-invalid")
        active = current["active_profile_id"]
        authority_path = PROFILE_STATE.with_name("authority.json")
        updated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        rebuilt = build_registry(load_authority(authority_path), updated)
        if active in {row["id"] for row in rebuilt["profiles"]}:
            rebuilt["active_profile_id"] = active
        store(PROFILE_STATE, rebuilt)
    except Exception:
        rollback_files(destination)
        raise
    finally:
        run("systemctl", "start", "kodi")
    for _ in range(30):
        try:
            rpc("Addons.SetAddonEnabled", {"addonid": "script.astertv.voice", "enabled": True})
            details = rpc("Addons.GetAddonDetails", {
                "addonid": "script.astertv.voice", "properties": ["enabled"]})
            if details.get("addon", {}).get("enabled") is True:
                break
        except (OSError, RuntimeError):
            pass
        import time
        time.sleep(0.2)
    else:
        raise RuntimeError("candidate-addon-not-enabled")
    print(json.dumps({"outcome": "installed", "target": EXPECTED_HOST,
                      "checkpoint": str(destination), "credential_output": False}, sort_keys=True))


def rollback_files(destination):
    report = json.loads((destination / "checkpoint.json").read_text())
    if ADDON.exists():
        shutil.rmtree(ADDON)
    if report.get("addon_preexisting"):
        shutil.copytree(destination / "addon", ADDON)
    for row in report["files"]:
        target = Path(row["path"])
        source = destination / "files" / target.relative_to("/")
        if digest(source) != row["sha256"]:
            raise RuntimeError("checkpoint-drift")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def rollback(identifier):
    if socket.gethostname() != EXPECTED_HOST or rpc("Player.GetActivePlayers"):
        raise RuntimeError("rollback-boundary")
    destination = CHECKPOINT_ROOT / identifier
    run("systemctl", "stop", "kodi")
    try:
        rollback_files(destination)
    finally:
        run("systemctl", "start", "kodi")
    print(json.dumps({"outcome": "rolled-back", "target": EXPECTED_HOST,
                      "checkpoint": str(destination)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("install")
    add.add_argument("--source", type=Path, required=True)
    add.add_argument("--checkpoint-id", required=True)
    undo = sub.add_parser("rollback")
    undo.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    if args.action == "install":
        install(args.source, args.checkpoint_id)
    else:
        rollback(args.checkpoint_id)


if __name__ == "__main__":
    main()
