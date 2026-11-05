#!/usr/bin/env python3
"""Materialize Bedroom's host-bound Wi-Fi stability unit."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/deploy/bedroom-wifi/astertv-wifi-stability.service"
DESTINATION = "storage/.config/system.d/astertv-wifi-stability.service"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render() -> tuple[bytes, dict]:
    data = SOURCE.read_bytes()
    text = data.decode()
    required = (
        "ConditionHost=AsterTV-Bedroom",
        "ConditionPathExists=/sys/class/net/wlan0",
        "ExecStart=/usr/sbin/iw dev wlan0 set power_save off",
        "ExecStop=/usr/sbin/iw dev wlan0 set power_save on",
    )
    if any(item not in text for item in required):
        raise RuntimeError("bedroom-wifi-unit-contract")
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "bedroom-wifi-stability",
        "targets": ["astertv-bedroom"],
        "files": [{
            "source": SOURCE.relative_to(CHECKOUT).as_posix(),
            "destination": "/" + DESTINATION,
            "bytes": len(data), "sha256": sha(data), "mode": "0644",
        }],
        "assertions": [{
            "authority": "libreelec", "key": "wifi.power-save",
            "expected": "disabled", "sensitive": False,
        }],
        "rollback": "disable unit, remove file, daemon-reload, restore power_save on",
    }
    return data, manifest


def write_tree(output: Path, data: bytes, manifest: dict) -> None:
    target = output / DESTINATION
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/bedroom-wifi-stability")
    args = parser.parse_args(argv)
    data, manifest = render()
    write_tree(args.output, data, manifest)
    print(json.dumps({"output": str(args.output), "files": 1,
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
