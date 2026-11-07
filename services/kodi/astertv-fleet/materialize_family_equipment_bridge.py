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
FAMILY_GATEWAY = HERE / "recovery/family/aster_remote-family-standby-20261106.py"
FILES = {
    # Family's accepted gateway deliberately remains separate from the broader
    # unreleased gateway candidate. This prevents a global source refresh from
    # silently replacing the live, owner-accepted standby/equipment behavior.
    "/opt/aster-agent/aster_remote.py": FAMILY_GATEWAY,
    **{"/opt/aster-agent/static/remote/" + path.relative_to(AGENT / "static/remote").as_posix(): path
       for path in sorted((AGENT / "static/remote").rglob("*")) if path.is_file()},
    **{"/config/custom_components/aster_room_bridge/" + path.relative_to(HA).as_posix(): path
       for path in sorted(HA.rglob("*")) if path.is_file()},
}
PINNED = {
    "/opt/aster-agent/aster_remote.py": "a064cfc5ea275e2f28c3c5d8e98cb2e3743a9a284ffe08760d91913304bb8518",
    "/opt/aster-agent/static/remote/app.js": "76a14595af2da756a72975eb02afe45cd21ac035d8b118dfc67a2635258e0762",
    "/config/custom_components/aster_room_bridge/__init__.py": "80df6f8e1cf9edf5d71c9d4540e32b4347ab8b13e9f249a0065c903e99cb40f3",
    "/config/custom_components/aster_room_bridge/content_policy.py": "4ed19eade495e4d35f7b58cb3b8b54dc21de2158a3b782139dda3a1af21a82f8",
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
            "aster_agent": "/var/lib/aster/checkpoints/astertv-v3-m7-family-standby-20261106/",
            "aster_agent_predecessor_sha256": "39d6239df804a86a74f187f6c24eb185f6fe9bd2e5a56fdab4bb20c5fcba1231",
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
