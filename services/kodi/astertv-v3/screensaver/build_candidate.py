#!/usr/bin/env python3
"""Build a deterministic, test-target-only AsterTV v3 screensaver bundle."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


HERE = Path(__file__).resolve().parent
PAYLOAD = (
    "addon.xml",
    "default.py",
    "policy.py",
    "service.py",
    "resources/skins/Default/1080i/AsterIdle.xml",
)
SKIN_DEPENDENCIES = (
    "special://skin/media/ui-solid.png",
    "special://skin/media/27-aster-media-logo.png",
    "special://skin/media/28-aster-books-logo.png",
    "special://skin/media/29-aster-music-logo.png",
    "special://skin/media/30-aster-news-logo.png",
    "special://skin/media/aster-home-logo-512.png",
    "special://skin/media/aster-compass-128.png",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest() -> dict:
    files = []
    for relative in PAYLOAD:
        data = (HERE / relative).read_bytes()
        files.append({"path": relative, "bytes": len(data), "sha256": digest(data)})
    return {
        "schema_version": 1,
        "identity": "screensaver.asterhome.v3",
        "status": "non-production-test-candidate",
        "release": False,
        "files": files,
        "skin_dependencies": list(SKIN_DEPENDENCIES),
        "forbidden_data": [
            "credentials", "camera imagery", "household state", "account data",
        ],
    }


def _tar_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mode = 0o644
    return info


def build(output: Path) -> dict:
    record = manifest()
    manifest_bytes = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for relative in PAYLOAD:
                    data = (HERE / relative).read_bytes()
                    archive.addfile(_tar_info("screensaver.asterhome.v3/" + relative, len(data)), io.BytesIO(data))
                archive.addfile(_tar_info("manifest.json", len(manifest_bytes)), io.BytesIO(manifest_bytes))
    return {"path": str(output), "bytes": output.stat().st_size,
            "sha256": digest(output.read_bytes()), "manifest": record}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

