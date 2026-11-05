#!/usr/bin/env python3
"""Materialize the accepted Aster Remote client for all three appliances."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/remote_client"
ADDON = SOURCE / "addon/service.asterremote"
TARGETS = {
    "astertv-family": {
        "stable": "/storage/.aster-v3/m8-remote", "apply": "apply_room_remote.py",
        "unit": "/storage/.config/system.d/astertv-v3-m8-remote.service",
        "unit_text": "[Unit]\nDescription=Apply Aster Remote room client\nBefore=kodi.service\n[Service]\nType=oneshot\nExecStart=/usr/bin/python3 /storage/.aster-v3/m8-remote/apply_room_remote.py\n[Install]\nWantedBy=kodi.service\n",
    },
    "astertv-bedroom": {
        "stable": "/storage/.aster-v3/m8-remote", "apply": "apply_room_remote.py",
        "unit": "/storage/.config/system.d/astertv-v3-m8-remote.service",
        "unit_text": "[Unit]\nDescription=Apply Aster Remote room client\nBefore=kodi.service\n[Service]\nType=oneshot\nExecStart=/usr/bin/python3 /storage/.aster-v3/m8-remote/apply_room_remote.py\n[Install]\nWantedBy=kodi.service\n",
    },
    "astertv-jen": {
        "stable": "/storage/.aster-v3/m8", "apply": "apply_remote_client.py",
        "unit": "/storage/.config/system.d/astertv-v3-m8-jen.service",
        "unit_text": "[Unit]\nDescription=Apply Aster Remote client on Jen\nAfter=astertv-v3-m6-jen.service\nBefore=kodi.service\n[Service]\nType=oneshot\nExecStart=/usr/bin/python3 /storage/.aster-v3/m8/apply_remote_client.py\n[Install]\nWantedBy=kodi.service\n",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def tree_sha(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for relative, data in sorted(files.items()):
        digest.update(relative.encode() + b"\0"); digest.update(data)
    return digest.hexdigest()


def render() -> tuple[dict[str, tuple[bytes, int]], dict]:
    addon = {path.relative_to(ADDON).as_posix(): path.read_bytes()
             for path in sorted(ADDON.rglob("*")) if path.is_file()}
    current_service = sha(addon["service.py"])
    if current_service != "0eba8fc5deaa22805a11c88b1fb402de552dcb876095cafd1610f9a4a5ab75ec":
        raise RuntimeError("remote-current-service-drift")
    addon_digest = tree_sha(addon)
    files: dict[str, tuple[bytes, int]] = {}
    rows = []

    def add(scope: str, output: str, destination: str, data: bytes, mode: int) -> None:
        files[output] = (data, mode)
        rows.append({"scope": scope, "destination": destination, "bytes": len(data),
                     "sha256": sha(data), "mode": format(mode, "04o")})

    for relative, data in sorted(addon.items()):
        add("common", "common/storage/.kodi/addons/service.asterremote/" + relative,
            "/storage/.kodi/addons/service.asterremote/" + relative, data, 0o644)
    for device_id, target in sorted(TARGETS.items()):
        prefix = f"targets/{device_id}"
        stable = target["stable"]
        for relative, data in sorted(addon.items()):
            add(device_id, prefix + stable + "/service.asterremote/" + relative,
                stable + "/service.asterremote/" + relative, data, 0o644)
        apply_source = SOURCE / target["apply"]
        add(device_id, prefix + stable + "/" + target["apply"],
            stable + "/" + target["apply"], apply_source.read_bytes(), 0o700)
        stable_manifest = (json.dumps({"schema": 1, "addon_sha256": addon_digest},
                                      sort_keys=True) + "\n").encode()
        add(device_id, prefix + stable + "/manifest.json", stable + "/manifest.json",
            stable_manifest, 0o600)
        unit = target["unit_text"].encode()
        add(device_id, prefix + target["unit"], target["unit"], unit, 0o644)
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "remote-client-v3",
        "targets": sorted(TARGETS),
        "files": sorted(rows, key=lambda row: (row["scope"], row["destination"])),
        "lineage": {
            "accepted_predecessor_sha256": "1a4d52f37f73290c21456342543ab871311d14031656dedafa22793ee46cfbce",
            "current_sha256": current_service,
            "evidence": "repository commit 90f2b3a8 and read-only parity on Family, Bedroom and Jen",
        },
        "mutable_state": [
            {"path": "/storage/.aster-private/asterremote-client.key", "bundled": False, "sensitive": True},
            {"path": "/storage/.aster-private/asterremote-client.json", "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/Database/Addons33.db", "bundled": False, "sensitive": False},
        ],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, tuple[bytes, int]], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, (data, mode) in sorted(files.items()):
        target = output / relative.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, mode); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/remote-client-v3")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
