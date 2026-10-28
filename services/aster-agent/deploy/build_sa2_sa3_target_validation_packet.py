#!/usr/bin/env python3
"""Build the exact source-and-tests packet for LXC104 Python validation."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import stat
import tarfile
from pathlib import Path

from build_sa2_sa3_composite_packet import ROOT, entries as release_entries


TESTS = {
    "services/aster-agent/test_sysadmin_followup_flow.py": "76cd7e6d92b0d77201ec0fafe8b6050b10d10eebcffc2a556cd7fa5b2f403be5",
    "services/aster-agent/test_sysadmin_followup_selector.py": "b3d70d9a2b6d4c5e4090372bca50bcaef5adbc894c61b7ad386a075e668e513f",
    "services/aster-agent/test_sysadmin_incident_store.py": "01c10b10f55a6c5d371189e5e2a4cf34aa1b614ca8e7b02536ddcdccd84473db",
    "services/aster-agent/test_sysadmin_incident_stream.py": "b9b3bd5289d45db1237a3907c096ec47d41bc8fdf37ec2bbfbec8c801f925583",
    "services/aster-agent/test_sysadmin_investigation.py": "029ac1e69a0edde70fec852e57b4bc965f2a60aaafd417a615268c380c48d4fa",
    "services/aster-agent/test_sysadmin_proposal_boundary.py": "f50115e57b974f6fc25f8d041efaf85871a26a82ca3d7af0ef40bf5b6b1ab56a",
    "services/aster-agent/test_sysadmin_proposal_gateway.py": "ebdafc8167be2a2f458f8bcd54298cd01b73f5785f6369e50de55139cbe0d93c",
    "services/aster-agent/test_sysadmin_proposal_transport.py": "532f7e3b2edfa43d5bfe87a1a13cd9f081ea433d1f23b5d46820f761f6a73711",
    "services/aster-agent/test_sysadmin_registered_producer.py": "cf63686d23edb5b898630f4adaba7d271ff9f6b13d2ebc710121fb99546b8147",
}

SUPPORT = {
    "evals/sysadmin-producer-fixture.json": (
        "services/aster-agent/evals/sysadmin-producer-fixture.json",
        "aec7e2f140898d54c4d7ec8b9010a8faeb3e4191b90c3661f7e040dcc3207233",
    ),
}


def _read_exact(path: Path, expected: str) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError("unsafe validation member")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read()
    finally:
        os.close(descriptor)
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("validation member hash mismatch")
    return raw


def entries(root: Path = ROOT) -> tuple[tuple[str, bytes], ...]:
    values = list(release_entries(root))
    for source, expected in TESTS.items():
        path = root / source
        values.append((path.name, _read_exact(path, expected)))
    for archive_name, (source, expected) in SUPPORT.items():
        values.append((archive_name, _read_exact(root / source, expected)))
    if len(values) != 17 or len({name for name, _ in values}) != 17:
        raise ValueError("invalid target-validation member set")
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
