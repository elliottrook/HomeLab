#!/usr/bin/env python3
"""Build a deterministic, non-installing Family content-gateway test bundle."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile


HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load(
    "astertv_m10_gateway_bundle",
    CHECKOUT / "services/kodi/astertv-v3/m10/build_gateway_test_bundle.py",
)
FAMILY = load("astertv_family_gateway_materializer", HERE / "materialize_family_equipment_bridge.py")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(output: Path) -> dict:
    sources = BASE.source_files()
    BASE.validate_sources(sources)
    derived = FAMILY.family_content_gateway()
    if sha256(derived) != FAMILY.PINNED["/opt/aster-agent/aster_remote.py"]:
        raise RuntimeError("derived-family-gateway-drift")

    payloads: list[tuple[str, bytes]] = []
    rows = []
    for path in sources:
        relative = path.relative_to(BASE.AGENT).as_posix()
        data = derived if relative == "aster_remote.py" else path.read_bytes()
        BASE.scan_payload(path, data)
        payloads.append((relative, data))
        rows.append({"path": relative, "bytes": len(data), "sha256": sha256(data)})

    manifest = {
        "schema_version": 1,
        "kind": "astertv-family-content-gateway-tests",
        "target": "Aster LXC 104 temporary directory",
        "service_mutation": False,
        "environment_file_loaded": False,
        "gateway_sha256": sha256(derived),
        "accepted_predecessor_sha256": FAMILY.FAMILY_GATEWAY_SHA256,
        "candidate_source_sha256": FAMILY.GATEWAY_CANDIDATE_SHA256,
        "files": rows,
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for relative, data in payloads:
                    archive.addfile(BASE.info(relative, len(data)), io.BytesIO(data))
                archive.addfile(BASE.info("manifest.json", len(encoded)), io.BytesIO(encoded))
    return {
        "path": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256(output.read_bytes()),
        "manifest": manifest,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

