#!/usr/bin/env python3
"""Materialize Family's exact G20 equipment and soft-standby keymap."""

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
CAPTURE = HERE / "peripherals/captures/astertv-family-g20-20261106.json"
RENDERER = CHECKOUT / "services/kodi/astertv-v3/remote_client/build_physical_equipment_keymap.py"
RELATIVE = "keymaps/z-astertv-v3-m7-family-equipment.xml"
DESTINATION = "/storage/.kodi/userdata/" + RELATIVE
EXPECTED_CODES = {
    "volume_down": 114,
    "volume_up": 115,
    "mute_toggle": 113,
    "power_toggle": 116,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_renderer():
    spec = importlib.util.spec_from_file_location("astertv_physical_keymap", RENDERER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[dict[str, tuple[bytes, int]], dict]:
    capture_bytes = CAPTURE.read_bytes()
    capture = json.loads(capture_bytes)
    if capture.get("hostname") != "AsterTV-Family":
        raise RuntimeError("family-capture-host")
    if capture.get("device", {}).get("usb_vid_pid") != "4842:0001":
        raise RuntimeError("family-capture-device")
    codes = {name: row.get("linux_code")
             for name, row in capture.get("observed", {}).items()}
    if codes != EXPECTED_CODES:
        raise RuntimeError("family-capture-codes")
    keymap = load_renderer().render(capture)
    files = {RELATIVE: (keymap, 0o644)}
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "family-physical-equipment-keys",
        "scope": "astertv-family",
        "capture": {"path": CAPTURE.relative_to(CHECKOUT).as_posix(),
                    "sha256": sha(capture_bytes)},
        "renderer": {"path": RENDERER.relative_to(CHECKOUT).as_posix(),
                     "sha256": sha(RENDERER.read_bytes())},
        "files": [{"scope": "astertv-family", "destination": DESTINATION,
                   "bytes": len(keymap), "sha256": sha(keymap), "mode": "0644"}],
        "mutable_state": [{
            "path": "/storage/.aster-private/astertv-standby.json",
            "bundled": False,
            "sensitive": False,
        }],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, tuple[bytes, int]], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, (data, mode) in sorted(files.items()):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, mode); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=HERE / "materialized/family-physical-equipment-keys")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
