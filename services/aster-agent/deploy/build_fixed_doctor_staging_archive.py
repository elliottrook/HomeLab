#!/usr/bin/env python3
"""Build a deterministic, source-only fixed-Doctor staging archive."""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import tarfile
from pathlib import Path

from validate_fixed_doctor_bundle import MANIFEST, ROOT, validate


SUPPORT = (
    "services/aster-agent/deploy/fixed-doctor-bundle-manifest.json",
    "services/aster-agent/deploy/validate_fixed_doctor_bundle.py",
)


def members() -> tuple[str, ...]:
    validate()
    manifest = json.loads(MANIFEST.read_text())
    paths = set(SUPPORT)
    paths.update(entry["source"] for entry in manifest["entries"])
    return tuple(sorted(paths))


def archive_bytes(root: Path = ROOT) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for relative in members():
                path = root / relative
                if not path.is_file() or path.is_symlink():
                    raise ValueError(f"unsafe staging member: {relative}")
                raw = path.read_bytes()
                info = tarfile.TarInfo(relative)
                info.size = len(raw)
                info.mode = 0o600
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                info.mtime = 0
                archive.addfile(info, io.BytesIO(raw))
    return output.getvalue()


def write_exclusive(path: Path, raw: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.output.is_absolute():
        raise SystemExit("output must be an absolute path")
    write_exclusive(args.output, archive_bytes())


if __name__ == "__main__":
    main()
