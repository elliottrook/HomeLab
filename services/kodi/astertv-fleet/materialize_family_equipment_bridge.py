#!/usr/bin/env python3
"""Materialize the external Family equipment bridge recovery payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
HA = CHECKOUT / "services/home-assistant/aster_room_bridge/custom_components/aster_room_bridge"
AGENT = CHECKOUT / "services/aster-agent"
FILES = {
    "/opt/aster-agent/aster_remote.py": AGENT / "aster_remote.py",
    **{"/opt/aster-agent/static/remote/" + path.relative_to(AGENT / "static/remote").as_posix(): path
       for path in sorted((AGENT / "static/remote").rglob("*")) if path.is_file()},
    **{"/config/custom_components/aster_room_bridge/" + path.relative_to(HA).as_posix(): path
       for path in sorted(HA.rglob("*")) if path.is_file()},
}
PINNED = {
    "/opt/aster-agent/aster_remote.py": "f2780775df560903ecf6a0b4efe224343f327914bd680fe8fdd4abb24484e983",
    "/opt/aster-agent/static/remote/app.js": "c4b3b371c18a7b3f53dad298ad8440f303b47f8c9c96cafbbb5c4c364e0df52b",
    "/config/custom_components/aster_room_bridge/__init__.py": "213a813d3c6b71ab5b6208223060bd24ed7f4a030a247aebe43bc0b012d95fac",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render() -> tuple[dict[str, tuple[bytes, int]], dict]:
    files = {}
    rows = []
    for destination, source in sorted(FILES.items()):
        data = source.read_bytes()
        if destination in PINNED and sha(data) != PINNED[destination]:
            raise RuntimeError("accepted-source-drift:" + destination)
        relative = "external" + destination
        files[relative] = (data, 0o644)
        rows.append({"scope": "external", "authority":
                     "home-assistant" if destination.startswith("/config/") else "aster-agent",
                     "destination": destination, "bytes": len(data),
                     "sha256": sha(data), "mode": "0644"})
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "family-equipment-bridge",
        "files": rows,
        "recovery": {
            "aster_agent": "/var/lib/aster/checkpoints/astertv-v3-m7-family-bridge-20261105/",
            "home_assistant": "/config/.aster-checkpoints/astertv-v3-m7-family-bridge-20261105/",
            "home_assistant_backup": "35b3cbd9",
            "opnsense_rule_uuid": "5e3a94b5-8059-45f7-b45c-f3b7484c4cf1",
        },
        "mutable_state": [
            {"path": "/etc/aster/remote-family-equipment.key", "bundled": False, "sensitive": True},
            {"path": "/config/.aster-private/aster-room-bridge.key", "bundled": False, "sensitive": True},
            {"authority": "home-assistant", "state": "configuration and entity registry", "bundled": False},
            {"authority": "opnsense", "state": "source-restricted firewall rule", "bundled": False},
        ],
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
            if os.path.exists(temporary): os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/family-equipment-bridge")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
