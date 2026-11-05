#!/usr/bin/env python3
"""Reapply only Jen's composed Home/Cameras presentation and lifecycle."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import socket
import subprocess

HOST = "AsterTV-Jen"
ROOT = Path("/storage/.aster-v3/m6")
KODI = Path("/storage/.kodi")
HOME = KODI / "addons/skin.asterhome/1080i/custom_1112_home.xml"
CAMERAS = KODI / "addons/skin.asterhome/1080i/custom_1134_cameras.xml"
CAMERA_RUNTIME = KODI / "addons/script.asterruntime/aster-camera2/view.py"
IDENTITY = Path("/storage/.aster-home/display-identity.json")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
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
    normalized = base[:-1] if base.endswith(b"\n") else base
    expected_home = overlay.transform_home(base)
    same_or_expected(HOME, normalized, expected_home)
    atomic(HOME, expected_home)
    atomic(CAMERAS, (ROOT / "custom_1134_cameras.xml").read_bytes())
    atomic(CAMERA_RUNTIME, (ROOT / "camera-view.py").read_bytes())
    marker = (ROOT / "display-identity.json").read_bytes()
    if IDENTITY.exists() and IDENTITY.read_bytes() != marker:
        raise RuntimeError("display-identity-drift")
    atomic(IDENTITY, marker, 0o600)
    subprocess.run(
        ["systemctl", "disable", "--now", "aster-camera.service"],
        check=True, capture_output=True, text=True,
    )


if __name__ == "__main__":
    main()
