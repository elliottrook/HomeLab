#!/usr/bin/env python3
"""Build a deterministic, secret-scanned SA-M10-C1 gateway test bundle."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile


ROOT = Path(__file__).resolve().parents[4]
AGENT = ROOT / "services/aster-agent"
FILES = (
    "aster_remote.py", "astertv_gateway.py", "astertv_with_delegation.py",
    "install_aster_remote.py", "install_aster_remote_headers.py",
    "install_aster_remote_reskin.py", "install_aster_remote_room_controls.py",
    "install_aster_remote_room_preference.py", "install_aster_remote_rooms.py",
    "install_astertv_gateway.py", "systemd/zz-asterremote.conf",
    "systemd/zz-astertv.conf", "test_aster_remote.py",
    "test_aster_remote_static.py", "test_astertv_gateway.py",
    "test_install_aster_remote.py", "test_install_aster_remote_headers.py",
    "test_install_aster_remote_reskin.py",
    "test_install_aster_remote_room_controls.py",
    "test_install_aster_remote_room_preference.py",
    "test_install_aster_remote_rooms.py", "test_install_astertv_gateway.py",
)
SECRET = re.compile(
    rb"(?i)(?:password|passwd|api[_ -]?key|access[_ -]?token|client[_ -]?secret)"
    rb"\s*[:=]\s*['\"][^'\"\r\n]{4,}"
)


def source_files() -> list[Path]:
    files = [AGENT / name for name in FILES]
    files.extend(sorted((AGENT / "static/remote").rglob("*")))
    return [path for path in files if path.is_file()]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def scan_payload(path: Path, data: bytes) -> None:
    if b"-----BEGIN " in data and b"PRIVATE KEY-----" in data:
        raise RuntimeError("private-key-in-gateway-test-bundle:" + str(path))
    for match in SECRET.finditer(data):
        value = match.group(0)
        # Source that constructs an environment assignment from a runtime value
        # is code, not an embedded credential. Literal assignments remain fatal.
        if (path.name == "install_astertv_gateway.py"
                and value.lower() == b'api_key=" + value + '):
            continue
        raise RuntimeError("credential-assignment-in-gateway-test-bundle:" + str(path))


def validate_sources(files: list[Path]) -> None:
    expected = {AGENT / name for name in FILES}
    missing = expected - set(files)
    if missing:
        raise RuntimeError("gateway-test-source-missing:" + ",".join(sorted(str(p) for p in missing)))
    for path in files:
        scan_payload(path, path.read_bytes())


def info(name: str, size: int) -> tarfile.TarInfo:
    row = tarfile.TarInfo(name)
    row.size = size
    row.mtime = row.uid = row.gid = 0
    row.uname = row.gname = ""
    row.mode = 0o644
    return row


def build(output: Path) -> dict:
    files = source_files()
    validate_sources(files)
    rows = []
    for path in files:
        data = path.read_bytes()
        rows.append({"path": path.relative_to(AGENT).as_posix(),
                     "bytes": len(data), "sha256": sha256(data)})
    manifest = {
        "schema_version": 1, "kind": "astertv-m10-gateway-tests",
        "target": "Aster LXC 104", "service_mutation": False,
        "environment_file_loaded": False, "files": rows,
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as raw:
        with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path, row in zip(files, rows):
                    data = path.read_bytes()
                    archive.addfile(info(row["path"], len(data)), io.BytesIO(data))
                archive.addfile(info("manifest.json", len(encoded)), io.BytesIO(encoded))
    return {"path": str(output), "bytes": output.stat().st_size,
            "sha256": sha256(output.read_bytes()), "manifest": manifest}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(build(args.output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

