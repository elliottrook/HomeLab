#!/usr/bin/env python3
"""Checkpoint and install the bounded Jen M4Y identity/lifecycle candidate."""

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


HOST = "AsterTV-Jen"
KODI = Path("/storage/.kodi")
YOUTUBE = KODI / "userdata/addon_data/plugin.video.youtube"
STAGED = Path("/storage/.aster-staging/m4y-youtube-state")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m4y-jen")
STABLE = Path("/storage/.aster-v3/m4y")
NAV = KODI / "addons/skin.asterhome/1080i/MyVideoNav.xml"
FOCUS = KODI / "addons/skin.asterhome/tools/youtube_root_focus.py"
ACCOUNT = KODI / "addons/script.asterprofiles.v3lab"
PROFILE_STATE = KODI / "userdata/addon_data/script.asterprofiles.v3lab"
DROPIN = Path("/storage/.config/system.d/kodi.service.d/50-astertv-graceful-stop.conf")
SERVICE = Path("/storage/.config/system.d/astertv-v3-m4y-jen.service")
DB = KODI / "userdata/Database/Addons33.db"
REQUIRED_STATE = {"access_manager.json", "api_keys.json", "settings.xml"}
BASE_NAV_SHA256 = "6798822d0218b96cde69e385545ad36a425c01c455fdfcb69a5d8ab7208fcf8a"


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        response = json.loads(connection.recv(65536))
    if "error" in response:
        raise RuntimeError("rpc:" + method)
    return response.get("result")


def private_state_valid(root):
    if {path.name for path in root.iterdir() if path.is_file()} != REQUIRED_STATE:
        raise RuntimeError("youtube-state-member-set")
    access = json.loads((root / "access_manager.json").read_text())
    keys = json.loads((root / "api_keys.json").read_text())
    manager = access.get("access_manager") if isinstance(access, dict) else None
    users = manager.get("users") if isinstance(manager, dict) else None
    current = manager.get("current_user") if isinstance(manager, dict) else None
    user = users.get(str(current)) if isinstance(users, dict) else None
    user_keys = keys.get("keys", {}).get("user") if isinstance(keys, dict) else None
    if not (isinstance(user, dict) and all(isinstance(user.get(name), str) and user[name]
            for name in ("id", "access_token", "refresh_token"))
            and isinstance(user_keys, dict) and all(isinstance(user_keys.get(name), str)
            and user_keys[name] for name in ("api_key", "client_id", "client_secret"))):
        raise RuntimeError("youtube-state-schema")
    return hashlib.sha256(user["id"].encode()).hexdigest()


def copy_any(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def checkpoint():
    if CHECKPOINT.exists():
        manifest = json.loads((CHECKPOINT / "checkpoint.json").read_text())
        if manifest.get("host") != HOST:
            raise RuntimeError("checkpoint-host-mismatch")
        return False
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    paths = (NAV, FOCUS, ACCOUNT / "identity_resolver.py", ACCOUNT / "authority.py",
             ACCOUNT / "registry.py", ACCOUNT / "service.py",
             PROFILE_STATE, DB, YOUTUBE, DROPIN, SERVICE)
    rows = []
    for source in paths:
        if not source.exists():
            continue
        saved = CHECKPOINT / "files" / source.relative_to("/")
        copy_any(source, saved)
        targets = [source] if source.is_file() else [p for p in source.rglob("*") if p.is_file()]
        for target in targets:
            rows.append({"path": str(target), "sha256": sha256(target)})
    manifest = {"schema": 1, "host": HOST, "youtube_state_present": YOUTUBE.exists(),
                "dropin_present": DROPIN.exists(), "service_present": SERVICE.exists(),
                "stable_present": STABLE.exists(),
                "files": rows}
    path = CHECKPOINT / "checkpoint.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.chmod(path, 0o600)
    return True


def restore_checkpoint():
    """Restore the exact pre-install surface recorded by the bounded checkpoint."""
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    manifest = json.loads((CHECKPOINT / "checkpoint.json").read_text())
    if manifest.get("host") != HOST:
        raise RuntimeError("checkpoint-host-mismatch")
    run("systemctl", "stop", "kodi")
    try:
        for target, present in ((YOUTUBE, manifest.get("youtube_state_present", False)),
                                (DROPIN, manifest.get("dropin_present", False)),
                                (SERVICE, manifest.get("service_present", False)),
                                (STABLE, manifest.get("stable_present", False))):
            if not present and target.exists():
                shutil.rmtree(target) if target.is_dir() else target.unlink()
        saved = CHECKPOINT / "files"
        for source in sorted(saved.rglob("*")):
            if source.is_file():
                destination = Path("/") / source.relative_to(saved)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        run("systemctl", "daemon-reload")
    finally:
        run("systemctl", "start", "kodi")
    print(json.dumps({"outcome": "rolled-back", "host": HOST}, sort_keys=True))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def install(source):
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    current_nav = sha256(NAV)
    if current_nav != BASE_NAV_SHA256:
        if not (STABLE / "MyVideoNav.base.xml").exists():
            raise RuntimeError("youtube-nav-base-drift")
        overlay = load("m4y_apply_resume", source / "apply_jen_m4y.py")
        expected = hashlib.sha256(
            overlay.patch_nav((STABLE / "MyVideoNav.base.xml").read_bytes())
        ).hexdigest()
        if current_nav != expected:
            raise RuntimeError("youtube-nav-overlay-drift")
    subject = private_state_valid(STAGED)
    addon_xml = KODI / "addons/plugin.video.youtube/addon.xml"
    if 'version="7.4.4"' not in addon_xml.read_text():
        raise RuntimeError("youtube-addon-version")
    checkpoint()
    STABLE.mkdir(parents=True, mode=0o700)
    payloads = {
        source / "apply_jen_m4y.py": STABLE / "apply_jen_m4y.py",
        source / "youtube_root_focus.py": STABLE / "youtube_root_focus.py",
        source / "graceful_kodi_stop.py": STABLE / "graceful_kodi_stop.py",
        source.parent / "accounts/identity_resolver.py": STABLE / "identity_resolver.py",
        source.parent / "accounts/authority.py": STABLE / "authority.py",
        source.parent / "accounts/registry.py": STABLE / "registry.py",
        source.parent / "accounts/addon/script.asterprofiles.v3lab/service.py":
            STABLE / "profile_service.py",
        NAV: STABLE / "MyVideoNav.base.xml",
    }
    for item, destination in payloads.items():
        shutil.copy2(item, destination); os.chmod(destination, 0o600)
    DROPIN.parent.mkdir(parents=True, exist_ok=True)
    DROPIN.write_text("[Service]\nExecStop=\nExecStop=/usr/bin/python3 /storage/.aster-v3/m4y/graceful_kodi_stop.py\nTimeoutStopSec=40\n")
    SERVICE.write_text("[Unit]\nDescription=Apply AsterTV v3 M4Y Jen overlay\nAfter=astertv-v3-m4-jen.service\nBefore=kodi.service\n[Service]\nType=oneshot\nExecStart=/usr/bin/python3 /storage/.aster-v3/m4y/apply_jen_m4y.py\n[Install]\nWantedBy=kodi.service\n")
    run("systemctl", "daemon-reload")
    # The newly loaded ExecStop performs the first graceful shutdown.
    run("systemctl", "stop", "kodi")
    try:
        if YOUTUBE.exists():
            shutil.rmtree(YOUTUBE)
        shutil.copytree(STAGED, YOUTUBE)
        for path in YOUTUBE.rglob("*"):
            if path.is_file(): os.chmod(path, 0o600)
        os.chmod(YOUTUBE, 0o700)
        run("python3", str(STABLE / "apply_jen_m4y.py"))
        authority = load("m4y_authority", ACCOUNT / "authority.py")
        registry = load("m4y_registry", ACCOUNT / "registry.py")
        config = authority.load_authority(PROFILE_STATE / "authority.json")
        state = authority.build_registry(config, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        state["active_profile_id"] = "jason"
        registry.store(PROFILE_STATE / "profiles.json", state)
        with sqlite3.connect(DB) as database:
            database.execute("UPDATE installed SET enabled=1 WHERE addonID='plugin.video.youtube'")
            database.commit()
        run("systemctl", "enable", "astertv-v3-m4y-jen.service")
        run("systemctl", "start", "kodi")
    except Exception:
        run("systemctl", "start", "kodi")
        raise
    print(json.dumps({"outcome": "installed", "host": HOST,
                      "youtube_subject_sha256": subject,
                      "credential_output": False, "guest_youtube": "denied"}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--source", type=Path)
    mode.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    restore_checkpoint() if args.rollback else install(args.source)


if __name__ == "__main__":
    main()
