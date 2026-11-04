#!/usr/bin/env python3
"""Checkpoint, install and roll back the Jen Guest catalogue candidate."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


HOST = "AsterTV-Jen"
KODI = Path("/storage/.kodi")
PROFILE = KODI / "addons/script.asterprofiles.v3lab"
PROFILE_STATE = KODI / "userdata/addon_data/script.asterprofiles.v3lab"
PROFILES = PROFILE_STATE / "profiles.json"
AUTHORITY = PROFILE_STATE / "authority.json"
GUEST = KODI / "addons/plugin.video.asterguest"
GUEST_STATE = KODI / "userdata/addon_data/plugin.video.asterguest"
KEYMAP = KODI / "userdata/keymaps/z-astertv-v3-m2-profile-gate.xml"
CREDENTIAL = Path("/storage/.aster-private/jellyfin-guest.json")
GUARD = Path("/storage/.aster-release/release_guard.py")
ACCEPTED = Path("/storage/.aster-release/accepted/accepted-manifest.json")
POLICY = Path("/storage/.aster-policy/jellyfin_client_policy.py")
CHECKPOINTS = Path("/storage/.aster-checkpoints")


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rpc(method, params=None):
    value = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        value["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=2) as connection:
        connection.sendall((json.dumps(value) + "\r\n").encode())
        raw = connection.recv(65536)
    response = json.loads(raw)
    if "error" in response:
        raise RuntimeError("json-rpc-error")
    return response.get("result")


def enable_guest_addon():
    """Wait for Kodi JSON-RPC, then make the installed adapter active."""
    for _ in range(30):
        try:
            rpc("Addons.SetAddonEnabled", {
                "addonid": "plugin.video.asterguest", "enabled": True,
            })
            details = rpc("Addons.GetAddonDetails", {
                "addonid": "plugin.video.asterguest", "properties": ["enabled"],
            })
            if details["addon"]["enabled"]:
                return
        except (ConnectionError, KeyError, OSError, RuntimeError):
            pass
        import time
        time.sleep(0.5)
    raise RuntimeError("guest-addon-not-enabled")


def require_boundary():
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    report = json.loads(run("python3", str(GUARD), "verify", "--host", HOST).stdout)
    if report.get("outcome") != "clean" or report.get("files") != 528:
        raise RuntimeError("release-guard-not-clean")
    if not CREDENTIAL.is_file() or CREDENTIAL.stat().st_mode & 0o077:
        raise RuntimeError("guest-credential-unavailable")


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def checkpoint(identifier):
    destination = CHECKPOINTS / identifier
    if destination.exists():
        raise RuntimeError("checkpoint-exists")
    destination.mkdir(parents=True, mode=0o700)
    sources = (PROFILE, PROFILE_STATE, KEYMAP, ACCEPTED, POLICY, CREDENTIAL)
    rows = []
    for source in sources:
        if not source.exists():
            raise RuntimeError("checkpoint-source-missing:" + str(source))
        copy(source, destination / "files" / source.relative_to("/"))
        paths = [source] if source.is_file() else sorted(source.rglob("*"))
        rows.extend({"path": str(path), "sha256": sha256(path)}
                    for path in paths if path.is_file())
    report = {"schema": 1, "host": HOST, "kind": "jen-guest-catalogue-checkpoint",
              "guest_addon_preexisting": GUEST.exists(), "files": rows}
    path = destination / "checkpoint.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(path, 0o600)
    return destination


def validate_archive(path, expected):
    if sha256(path) != expected:
        raise RuntimeError("candidate-sha256")
    with tarfile.open(path, "r:gz") as bundle:
        for member in bundle.getmembers():
            relative = PurePosixPath(member.name)
            if not member.isfile() or relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError("unsafe-candidate-member")
        manifest = json.load(bundle.extractfile(
            "astertv-v3-m2-jen-guest/manifest.json"
        ))
    if manifest.get("target") != HOST or manifest.get("release") is not False:
        raise RuntimeError("candidate-boundary")
    return manifest


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def restore(destination):
    report = json.loads((destination / "checkpoint.json").read_text())
    if report.get("host") != HOST:
        raise RuntimeError("checkpoint-host")
    for row in report["files"]:
        source = destination / "files" / Path(row["path"]).relative_to("/")
        if sha256(source) != row["sha256"]:
            raise RuntimeError("checkpoint-drift")
    for target in (PROFILE, PROFILE_STATE, GUEST, GUEST_STATE):
        if target.exists():
            shutil.rmtree(target)
    KEYMAP.unlink(missing_ok=True)
    for source in (PROFILE, PROFILE_STATE, KEYMAP, ACCEPTED, POLICY, CREDENTIAL):
        copy(destination / "files" / source.relative_to("/"), source)


def install(archive, expected, identifier):
    require_boundary(); manifest = validate_archive(archive, expected)
    destination = checkpoint(identifier)
    run("systemctl", "stop", "kodi")
    try:
        with tempfile.TemporaryDirectory(prefix="astertv-guest-", dir="/storage/.aster-staging") as temp:
            with tarfile.open(archive, "r:gz") as bundle:
                bundle.extractall(temp)
            root = Path(temp) / "astertv-v3-m2-jen-guest"
            for source, target in ((root / "addons/script.asterprofiles.v3lab", PROFILE),
                                   (root / "addons/plugin.video.asterguest", GUEST)):
                if target.exists():
                    shutil.rmtree(target)
                staging = target.with_name("." + target.name + ".installing")
                shutil.copytree(source, staging)
                for path in staging.rglob("*"):
                    if path.is_file(): os.chmod(path, 0o644)
                os.replace(staging, target)
            shutil.copy2(root / "keymaps/z-astertv-v3-m2-profile-gate.xml", KEYMAP)
            sys.path.insert(0, str(PROFILE))
            registry = module("guest_registry", PROFILE / "registry.py")
            authority = module("guest_authority", PROFILE / "authority.py")
            config = authority.load_authority(AUTHORITY)
            registry.store(PROFILES, authority.build_registry(config, now()))
        run("systemctl", "start", "kodi")
        enable_guest_addon()
    except Exception:
        run("systemctl", "stop", "kodi")
        restore(destination)
        run("systemctl", "start", "kodi")
        raise
    print(json.dumps({"outcome": "installed", "target": HOST,
                      "candidate_sha256": expected, "checkpoint": str(destination),
                      "kind": manifest["kind"], "credential_output": False}, sort_keys=True))


def rollback(identifier):
    if socket.gethostname() != HOST or rpc("Player.GetActivePlayers"):
        raise RuntimeError("rollback-boundary")
    destination = CHECKPOINTS / identifier
    run("systemctl", "stop", "kodi")
    try:
        restore(destination); run("systemctl", "start", "kodi")
    except Exception:
        run("systemctl", "start", "kodi"); raise
    print(json.dumps({"outcome": "rolled-back", "target": HOST,
                      "checkpoint": str(destination)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(); commands = parser.add_subparsers(dest="action", required=True)
    add = commands.add_parser("install")
    add.add_argument("--archive", type=Path, required=True); add.add_argument("--sha256", required=True)
    add.add_argument("--checkpoint-id", required=True)
    remove = commands.add_parser("rollback"); remove.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    if args.action == "install": install(args.archive, args.sha256, args.checkpoint_id)
    else: rollback(args.checkpoint_id)


if __name__ == "__main__":
    main()
