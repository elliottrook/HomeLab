#!/usr/bin/env python3
"""Build a deterministic seven-file SA2/SA3 target packet."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import stat
import tarfile
from pathlib import Path

from validate_sa2_sa3_composite_bundle import ROOT, validate


ENTRIES = {
    "/opt/aster-agent/aster_agent.py": {
        "source": "services/aster-agent/aster_agent.py",
        "sha256": "02a2001caee5204b6229f7f576dcc945227471ac531b852f0ab0f60ecb032f9b",
    },
    "/opt/aster-agent/doctor_incident_adapter.py": {
        "source": "services/aster-agent/doctor_incident_adapter.py",
        "sha256": "0baece59b29dcee47395dbc42bab742ba33fa0d3ad708ffedc41c22a2ae23968",
    },
    "/opt/aster-agent/sysadmin_incident_store.py": {
        "source": "services/aster-agent/sysadmin_incident_store.py",
        "sha256": "5676b4b865b5ff9100802967dbce1a455aa6a4d8815ac0e489dc09e368978328",
    },
    "/opt/aster-agent/sysadmin_registered_producer.py": {
        "source": "services/aster-agent/sysadmin_registered_producer.py",
        "sha256": "3291feaaace83a42f98f578f29e0b2831a82c8b1cae31793a0cdb0b4a622353a",
    },
    "/opt/aster-agent/sysadmin_proposal_boundary.py": {
        "source": "services/aster-agent/sysadmin_proposal_boundary.py",
        "sha256": "121d61c12c2f33368176ec35bcc0047f075c1d21d4640749658bf509fce813ff",
    },
    "/opt/aster-agent/sysadmin_proposal_transport.py": {
        "source": "services/aster-agent/sysadmin_proposal_transport.py",
        "sha256": "9b4d98df78c69e360e2f59544a47152c7eefc58bcad7f33e74e917158c24e4fa",
    },
    "/opt/aster-agent/sysadmin_proposal_gateway.py": {
        "source": "services/aster-agent/sysadmin_proposal_gateway.py",
        "sha256": "4a4d112e8dcb805f5cdead1cedbfca9229b57eb7066ce7b7a5164138c9a5bd9c",
    },
}


def entries(root: Path = ROOT) -> tuple[tuple[str, bytes], ...]:
    validate()
    values = []
    for target, expected in ENTRIES.items():
        name = Path(target).name
        source = root / str(expected["source"])
        if source.name != name:
            raise ValueError("unsafe or mismatched packet member")
        descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                raise ValueError("unsafe packet member")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                raw = stream.read()
        finally:
            os.close(descriptor)
        if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            raise ValueError("packet source hash mismatch")
        values.append((name, raw))
    if len({name for name, _ in values}) != 7:
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
