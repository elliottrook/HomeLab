#!/usr/bin/env python3
"""Repair Jen's semantic Home display identity resolver, with rollback custody."""

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
PREDECESSOR = "131046f36532bac15c2a714f41bc4929c3fcc64f84ec7424318db95b49c0d872"
TARGET = "6c7f1ae41212f0c6360a6440b662a593c7286f79331e5d8cf0fcf2d7700900ef"
LIVE = Path("/storage/.kodi/addons/script.asterprofiles.v3lab/identity_resolver.py")
STABLE = Path("/storage/.aster-v3/m6/identity_resolver.py")
MARKER = Path("/storage/.aster-home/display-identity.json")
REGISTRY = Path("/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab/profiles.json")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-home-identity-semantic-20261106")
REPORT = Path("/storage/.aster-v3/m10/jen-home-identity-repair.json")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        response = json.loads(connection.recv(65536))
    if "error" in response:
        raise RuntimeError("rpc:" + method)
    return response.get("result")


def home_subject():
    value = json.loads(MARKER.read_text(encoding="utf-8"))
    if (not isinstance(value, dict)
            or set(value) != {"schema", "kind", "authority"}
            or value.get("schema") != 1
            or value.get("kind") != "astertv-home-display"
            or value.get("authority") != "ha-home-dashboard-v4"):
        raise RuntimeError("display-identity-invalid")
    canonical = (json.dumps(value, sort_keys=True) + "\n").encode()
    return "local:home-assistant:display:sha256:" + hashlib.sha256(canonical).hexdigest()


def verify_registry(subject):
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = [mapping for profile in data.get("profiles", ())
            if profile.get("id") == "jason" and profile.get("role") == "recovery_admin"
            for mapping in profile.get("service_mappings", ())
            if mapping.get("service") == "home_assistant"]
    if len(rows) != 1 or rows[0].get("enabled") is not True or rows[0].get("opaque_subject_id") != subject:
        raise RuntimeError("home-authority-registry-drift")


def atomic(source, destination):
    temporary = destination.with_name("." + destination.name + ".semantic-identity")
    shutil.copy2(source, temporary)
    os.chmod(temporary, 0o644)
    os.replace(temporary, destination)


def store_report(value):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temporary = REPORT.with_name("." + REPORT.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, REPORT)


def wait_kodi(timeout=35):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if rpc("Player.GetActivePlayers") == []:
                return
        except (OSError, ValueError, RuntimeError):
            pass
        time.sleep(0.5)
    raise RuntimeError("kodi-restart-timeout")


def wait_profile(timeout=25):
    label = "Window(Home).Property(Aster.Profile.State)"
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            labels = rpc("XBMC.GetInfoLabels", {"labels": [label]})
            last = labels.get(label) if isinstance(labels, dict) else None
            if last:
                return last
        except (OSError, ValueError, RuntimeError):
            pass
        time.sleep(0.5)
    raise RuntimeError("profile-state-timeout:" + str(last))


def install(source):
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if sha(source) != TARGET:
        raise RuntimeError("candidate-drift")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    subject = home_subject()
    verify_registry(subject)
    before = {"live": sha(LIVE), "stable": sha(STABLE)}
    if set(before.values()) == {TARGET}:
        store_report({"schema": 1, "host": HOST, "outcome": "already-installed",
                      "files": before, "subject": subject})
        return
    if set(before.values()) != {PREDECESSOR}:
        raise RuntimeError("predecessor-drift")
    if CHECKPOINT.exists():
        manifest = json.loads((CHECKPOINT / "checkpoint.json").read_text())
        if manifest != {"schema": 1, "host": HOST, "files": before}:
            raise RuntimeError("checkpoint-drift")
    else:
        CHECKPOINT.mkdir(parents=True, mode=0o700)
        shutil.copy2(LIVE, CHECKPOINT / "live.py")
        shutil.copy2(STABLE, CHECKPOINT / "stable.py")
        (CHECKPOINT / "checkpoint.json").write_text(json.dumps(
            {"schema": 1, "host": HOST, "files": before}, indent=2, sort_keys=True) + "\n")
        os.chmod(CHECKPOINT / "checkpoint.json", 0o600)
    atomic(source, LIVE)
    atomic(source, STABLE)
    try:
        subprocess.run(["systemctl", "restart", "kodi"], check=True, timeout=40)
        wait_kodi()
        state = wait_profile()
        if state != "resolved":
            raise RuntimeError("profile-state:" + str(state))
        after = {"live": sha(LIVE), "stable": sha(STABLE)}
        if set(after.values()) != {TARGET} or rpc("Player.GetActivePlayers"):
            raise RuntimeError("post-install-drift")
        store_report({"schema": 1, "host": HOST, "outcome": "installed",
                      "before": before, "after": after, "subject": subject,
                      "profile_state": state})
    except Exception:
        atomic(CHECKPOINT / "live.py", LIVE)
        atomic(CHECKPOINT / "stable.py", STABLE)
        subprocess.run(["systemctl", "restart", "kodi"], check=False, timeout=40)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args(argv)
    install(args.source)
    print(REPORT.read_text(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
