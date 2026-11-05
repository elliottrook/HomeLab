#!/usr/bin/env python3
"""Materialize Jen Home/Cameras without account, voice or secret state."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/m6"
BASE = SOURCE / "fixtures/custom_1112_home.predecessor.xml"
OVERLAY = SOURCE / "home_overlay.py"
APPLY = SOURCE / "apply_jen_home_cameras_composed.py"
CAMERAS = SOURCE / "addon/skin/custom_1134_cameras.xml"
VIEW = SOURCE / "addon/aster-camera2/view.py"
BASE_SHA256 = "ec3cae3a5bc7f2c687b2cd3d997947d3f2f76e195fb4b61243b1941db677266f"
FINAL_HOME_SHA256 = "dbce098a14ccd1e2e85552c8f3e43e396d4dc9fb64b64429225dadc7ab1b5c97"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_overlay():
    spec = importlib.util.spec_from_file_location("astertv_m6_overlay", OVERLAY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[dict[str, tuple[bytes, str, str]], dict]:
    base = BASE.read_bytes()
    normalized = base[:-1] if base.endswith(b"\n") else base
    if sha(normalized) != BASE_SHA256:
        raise RuntimeError("jen-home-base-drift")
    home = load_overlay().transform_home(base)
    if sha(home) != FINAL_HOME_SHA256:
        raise RuntimeError("jen-home-render-drift")
    marker = canonical({"authority": "ha-home-dashboard-v4",
                        "kind": "astertv-home-display", "schema": 1})
    unit = (
        "[Unit]\nDescription=Apply AsterTV v3 M6 Home and Cameras on Jen\n"
        "After=astertv-v3-m5p-jen.service\nBefore=kodi.service\n"
        "[Service]\nType=oneshot\n"
        "ExecStart=/usr/bin/python3 /storage/.aster-v3/m6/apply_jen_home_cameras.py\n"
        "[Install]\nWantedBy=kodi.service\n"
    ).encode()
    files = {
        "skin.asterhome/1080i/custom_1112_home.xml":
            (home, "/storage/.kodi/addons/skin.asterhome/1080i/custom_1112_home.xml", "0644"),
        "skin.asterhome/1080i/custom_1134_cameras.xml":
            (CAMERAS.read_bytes(), "/storage/.kodi/addons/skin.asterhome/1080i/custom_1134_cameras.xml", "0644"),
        "script.asterruntime/aster-camera2/view.py":
            (VIEW.read_bytes(), "/storage/.kodi/addons/script.asterruntime/aster-camera2/view.py", "0644"),
        "aster-home/display-identity.json":
            (marker, "/storage/.aster-home/display-identity.json", "0600"),
        "stable/Home.base.xml":
            (base, "/storage/.aster-v3/m6/Home.base.xml", "0600"),
        "stable/custom_1134_cameras.xml":
            (CAMERAS.read_bytes(), "/storage/.aster-v3/m6/custom_1134_cameras.xml", "0600"),
        "stable/camera-view.py":
            (VIEW.read_bytes(), "/storage/.aster-v3/m6/camera-view.py", "0600"),
        "stable/home_overlay.py":
            (OVERLAY.read_bytes(), "/storage/.aster-v3/m6/home_overlay.py", "0600"),
        "stable/apply_jen_home_cameras.py":
            (APPLY.read_bytes(), "/storage/.aster-v3/m6/apply_jen_home_cameras.py", "0600"),
        "stable/display-identity.json":
            (marker, "/storage/.aster-v3/m6/display-identity.json", "0600"),
        "system.d/astertv-v3-m6-jen.service":
            (unit, "/storage/.config/system.d/astertv-v3-m6-jen.service", "0644"),
    }
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-home-cameras",
        "provenance": {"checkpoint": "astertv-v3-m6-jen",
                       "base_sha256": BASE_SHA256,
                       "renderer_sha256": sha(OVERLAY.read_bytes())},
        "files": [
            {"destination": destination, "bytes": len(data),
             "sha256": sha(data), "mode": mode}
            for _, (data, destination, mode) in sorted(files.items())
        ],
        "mutable_state": [
            {"path": "/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab/profiles.json",
             "bundled": False, "sensitive": True, "owner": "jen-account-registry"},
            {"path": "/storage/.aster-private/home-feed.key", "bundled": False, "sensitive": True},
            {"path": "/storage/.aster-private/camera-viewer.key", "bundled": False, "sensitive": True},
            {"path": "/storage/.aster-camera", "bundled": False, "sensitive": True},
        ],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, tuple[bytes, str, str]], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, (data, _, mode) in sorted(files.items()):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, int(mode, 8)); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-home-cameras")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
