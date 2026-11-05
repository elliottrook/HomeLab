#!/usr/bin/env python3
"""Reapply Jen's read-only Home/Cameras overlay after earlier boot overlays."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess


HOST = "AsterTV-Jen"
ROOT = Path("/storage/.aster-v3/m6")
KODI = Path("/storage/.kodi")
SKIN = KODI / "addons/skin.asterhome/1080i"
HOME = SKIN / "custom_1112_home.xml"
CAMERAS = SKIN / "custom_1134_cameras.xml"
CAMERA_RUNTIME = KODI / "addons/script.asterruntime/aster-camera2/view.py"
PROFILES_ADDON = KODI / "addons/script.asterprofiles.v3lab"
VOICE = KODI / "addons/script.astertv.voice/default.py"
PROFILE_STATE = KODI / "userdata/addon_data/script.asterprofiles.v3lab/profiles.json"
IDENTITY = Path("/storage/.aster-home/display-identity.json")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def atomic(destination, payload, mode=0o644):
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name("." + destination.name + ".m6")
    temporary.write_bytes(payload)
    os.chmod(temporary, mode)
    os.replace(temporary, destination)


def same_or_expected(destination, base, expected):
    current = destination.read_bytes()
    if current not in (base, expected):
        raise RuntimeError("live-drift:" + destination.name)


def main():
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    overlay = load("m6_overlay_runtime", ROOT / "home_overlay.py")
    base = (ROOT / "Home.base.xml").read_bytes()
    expected_home = overlay.transform_home(base)
    same_or_expected(HOME, base[:-1] if base.endswith(b"\n") else base, expected_home)
    replacements = {
        CAMERAS: ROOT / "custom_1134_cameras.xml",
        CAMERA_RUNTIME: ROOT / "camera-view.py",
        PROFILES_ADDON / "addon.xml": ROOT / "profile-addon.xml",
        PROFILES_ADDON / "registry.py": ROOT / "registry.py",
        PROFILES_ADDON / "access_policy.py": ROOT / "access_policy.py",
        PROFILES_ADDON / "authority.py": ROOT / "authority.py",
        PROFILES_ADDON / "identity_resolver.py": ROOT / "identity_resolver.py",
        VOICE: ROOT / "astertv-voice.py",
    }
    atomic(HOME, expected_home)
    for destination, source in replacements.items():
        atomic(destination, source.read_bytes())
    marker = (ROOT / "display-identity.json").read_bytes()
    if IDENTITY.exists() and IDENTITY.read_bytes() != marker:
        raise RuntimeError("display-identity-drift")
    atomic(IDENTITY, marker, 0o600)
    registry = load("m6_registry_runtime", PROFILES_ADDON / "registry.py")
    current, status = registry.load(PROFILE_STATE)
    if status != "valid":
        raise RuntimeError("profile-registry-invalid")
    subject = overlay.display_subject(marker)
    admin = next((row for row in current["profiles"]
                  if row.get("id") == "jason" and row.get("role") == "recovery_admin"), None)
    mappings = [] if admin is None else [row for row in admin["service_mappings"]
                                         if row.get("service") == "home_assistant"]
    if not mappings:
        current = overlay.extend_registry(current, subject)
        current["updated_at"] = datetime.now(timezone.utc).replace(
            microsecond=0).isoformat().replace("+00:00", "Z")
        registry.store(PROFILE_STATE, current)
    elif (len(mappings) != 1 or mappings[0].get("opaque_subject_id") != subject
          or mappings[0].get("enabled") is not True
          or not {"home_status", "camera_view"} <= set(admin.get("entitlements", []))
          or {"home_control", "cameras"} & set(admin.get("entitlements", []))):
        raise RuntimeError("home-profile-authority-drift")
    registry.validate(current)
    # The camera proxy is an on-demand capability, not a boot daemon.  The
    # Cameras window starts it explicitly and stops it on leave; disabling the
    # unit here also repairs older clients where the source service was left
    # enabled before M6 separated Cameras from Home.
    subprocess.run(
        ["systemctl", "disable", "--now", "aster-camera.service"],
        check=True,
        capture_output=True,
        text=True,
    )


if __name__ == "__main__":
    main()
