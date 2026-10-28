#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import io
import os
import stat
import tarfile
from pathlib import Path

from validate_sa1_sa3_forgejo_expansion import ROOT, validate


def entries(root: Path = ROOT):
    release = validate(root)
    values = []
    for item in release["files"]:
        source = root / item["source"]
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("unsafe packet member")
            raw = os.read(descriptor, metadata.st_size + 1)
        finally:
            os.close(descriptor)
        values.append((source.name, raw))
    return tuple(sorted(values))


def packet_bytes() -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, raw in entries():
                info = tarfile.TarInfo(name)
                info.size = len(raw); info.mode = 0o600; info.uid = info.gid = 0
                info.uname = info.gname = "root"; info.mtime = 0
                archive.addfile(info, io.BytesIO(raw))
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("output", type=Path)
    output = parser.parse_args().output
    if not output.is_absolute():
        raise SystemExit("output must be absolute")
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(packet_bytes()); stream.flush(); os.fsync(stream.fileno())


if __name__ == "__main__":
    main()
