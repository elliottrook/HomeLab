#!/usr/bin/env python3
"""Materialize target-aware release-guard payloads without touching a client."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/reliability"
TARGETS = {
    "astertv-family": "AsterTV-Family",
    "astertv-bedroom": "AsterTV-Bedroom",
    "astertv-jen": "AsterTV-Jen",
}
COMMON = {
    SOURCE / "release_guard.py": "storage/.aster-release/release_guard.py",
    SOURCE / "service.aster.reliability/addon.xml": "storage/.kodi/addons/service.aster.reliability/addon.xml",
    SOURCE / "service.aster.reliability/recovery_policy.py": "storage/.kodi/addons/service.aster.reliability/recovery_policy.py",
    SOURCE / "service.aster.reliability/service.py": "storage/.kodi/addons/service.aster.reliability/service.py",
}
UNIT_SOURCE = SOURCE / "astertv-release-guard.service"
UNIT_DESTINATION = "storage/.config/system.d/astertv-release-guard.service"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render() -> tuple[dict[str, tuple[bytes, int]], dict]:
    unit = UNIT_SOURCE.read_bytes()
    marker = b"--host %H"
    if unit.count(marker) != 1:
        raise RuntimeError("release-guard-unit-host-marker")
    files: dict[str, tuple[bytes, int]] = {}
    manifest_files = []
    for source, destination in sorted(COMMON.items(), key=lambda row: row[1]):
        data = source.read_bytes()
        mode = 0o700 if source.name == "release_guard.py" else 0o644
        output = "common/" + destination
        files[output] = (data, mode)
        manifest_files.append({"scope": "common", "source": source.relative_to(CHECKOUT).as_posix(),
                               "destination": "/" + destination, "bytes": len(data),
                               "sha256": sha(data), "mode": format(mode, "04o")})
    for device_id, hostname in sorted(TARGETS.items()):
        data = unit.replace(marker, b"--host " + hostname.encode("ascii"))
        output = f"targets/{device_id}/{UNIT_DESTINATION}"
        files[output] = (data, 0o644)
        manifest_files.append({"scope": device_id, "source": UNIT_SOURCE.relative_to(CHECKOUT).as_posix(),
                               "destination": "/" + UNIT_DESTINATION, "bytes": len(data),
                               "sha256": sha(data), "mode": "0644",
                               "render": {"hostname": hostname}})
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "release-guard-v1",
        "targets": sorted(TARGETS),
        "files": sorted(manifest_files, key=lambda row: (row["scope"], row["destination"])),
        "generated_state": [{
            "path": "/storage/.aster-release/accepted",
            "owner": "release-guard-v1",
            "method": "host-bound-snapshot-after-idle-acceptance",
            "bundled": False,
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
            os.chmod(temporary, mode)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/release-guard-v1")
    args = parser.parse_args(argv)
    files, manifest = render()
    write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
