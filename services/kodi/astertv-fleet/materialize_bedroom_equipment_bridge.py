#!/usr/bin/env python3
"""Materialize Bedroom's accepted HA bridge and restricted LG wake relay."""

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
WAKE = HERE / "recovery/bedroom/astertv-bedroom-lg-wake"
INIT_SHA256 = "66843f8b304f59cc298dfd722fdb947ab797a8c927cd8c1366d0d671462adba3"
WAKE_SHA256 = "939fe37af159d5d703e822e48df82f5f097c27c3798888b89f30cce9d27c1973"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render() -> tuple[dict[str, tuple[bytes, int]], dict]:
    init = HA / "__init__.py"
    if sha(init.read_bytes()) != INIT_SHA256:
        raise RuntimeError("bedroom-ha-bridge-source-drift")
    if sha(WAKE.read_bytes()) != WAKE_SHA256:
        raise RuntimeError("bedroom-wake-helper-source-drift")

    files: dict[str, tuple[bytes, int]] = {}
    rows = []
    for source in sorted(HA.rglob("*")):
        if not source.is_file() or source.suffix == ".pyc" or "__pycache__" in source.parts:
            continue
        destination = "/config/custom_components/aster_room_bridge/" + source.relative_to(HA).as_posix()
        relative = "external/home-assistant" + destination
        data = source.read_bytes()
        files[relative] = (data, 0o644)
        rows.append({"scope": "external", "authority": "home-assistant",
                     "destination": destination, "bytes": len(data),
                     "sha256": sha(data), "mode": "0644"})

    wake_data = WAKE.read_bytes()
    wake_destination = "/usr/local/sbin/astertv-bedroom-lg-wake"
    files["external/opnsense" + wake_destination] = (wake_data, 0o755)
    rows.append({"scope": "external", "authority": "opnsense",
                 "destination": wake_destination, "bytes": len(wake_data),
                 "sha256": sha(wake_data), "mode": "0755"})

    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "bedroom-equipment-bridge",
        "files": sorted(rows, key=lambda row: (row["authority"], row["destination"])),
        "recovery": {
            "home_assistant_configuration": "/config/configuration.yaml.astertv-bedroom-wol-relay-20261107.bak",
            "home_assistant_component": "/config/custom_components/aster_room_bridge/__init__.py.astertv-bedroom-wol-direct-20261107.bak",
            "opnsense_config": "/conf/backup/config-astertv-bedroom-wol-before-20261107.xml",
            "opnsense_authorized_keys": "/root/.ssh/authorized_keys.astertv-bedroom-lg-dualwake-20261107.bak",
        },
        "mutable_state": [
            {"authority": "home-assistant", "path": "/config/.ssh/astertv_bedroom_wol", "bundled": False, "sensitive": True},
            {"authority": "home-assistant", "path": "/config/.aster-private/aster-room-bridge-bedroom.key", "bundled": False, "sensitive": True},
            {"authority": "home-assistant", "state": "Bedroom room row plus fixed shell_command", "bundled": False, "sensitive": False},
            {"authority": "opnsense", "state": "rule 2c486e0a-6db5-4a31-9bb0-bf512dd12a01 and forced-command public key", "bundled": False, "sensitive": False},
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
            if os.path.exists(temporary):
                os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=HERE / "materialized/bedroom-equipment-bridge")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
