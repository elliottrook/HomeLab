#!/usr/bin/env python3
"""Build the deterministic three-file SA2 Doctor producer target packet."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import stat
import tarfile
from pathlib import Path

from validate_sa2_doctor_producer_bundle import ENTRIES, ROOT, validate


def entries(root: Path = ROOT) -> tuple[tuple[str, bytes], ...]:
    validate()
    values = []
    for target, expected in ENTRIES.items():
        name = Path(target).name
        source = root / expected["source"]
        if source.name != name:
            raise ValueError("unsafe or mismatched packet member")
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("unsafe or mismatched packet member")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                raw = stream.read()
        finally:
            os.close(descriptor)
        if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            raise ValueError("packet source hash mismatch")
        values.append((name, raw))
    if len({name for name, _ in values}) != len(values):
        raise ValueError("duplicate packet member")
    return tuple(sorted(values))


def packet_bytes() -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, raw in entries():
                info = tarfile.TarInfo(name)
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
        raise SystemExit("output must be absolute")
    write_exclusive(args.output, packet_bytes())


if __name__ == "__main__":
    main()
