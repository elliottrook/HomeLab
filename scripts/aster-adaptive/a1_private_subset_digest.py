"""Content-free, read-only digest for the fixed A1 backup subset.

This is an observation helper. It neither authenticates its caller nor creates
an admission receipt. Keep raw paths and per-file hashes out of stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import time
from pathlib import Path


class ScanError(ValueError):
    pass


def _rows(root: Path, *, max_files: int, max_bytes: int) -> list[tuple[str, int, str]]:
    if not stat.S_ISDIR(os.lstat(root).st_mode):
        raise ScanError("subset root is not a real directory")
    rows: list[tuple[str, int, str]] = []
    total = 0
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISDIR(mode):
                    pending.append(Path(entry.path))
                    continue
                if not stat.S_ISREG(mode):
                    raise ScanError("subset contains a non-regular entry")
                size = entry.stat(follow_symlinks=False).st_size
                if size < 0 or len(rows) >= max_files or total + size > max_bytes:
                    raise ScanError("subset exceeds fixed scan bounds")
                digest = hashlib.sha256()
                with open(entry.path, "rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        digest.update(chunk)
                if entry.stat(follow_symlinks=False).st_size != size:
                    raise ScanError("subset changed during scan")
                rows.append((Path(entry.path).relative_to(root).as_posix(), size, digest.hexdigest()))
                total += size
    if not rows:
        raise ScanError("subset is empty")
    rows.sort(key=lambda row: row[0])
    return rows


def scan(root: Path, *, max_files: int = 9, max_bytes: int = 1_000_000) -> dict[str, object]:
    """Return only count, bytes and a canonical manifest digest.

    Two consecutive scans must agree so a changing directory fails closed.
    This cannot prevent a malicious local writer from racing or fabricating a
    result; the trusted producer/identity remains a separate platform gate.
    """
    first = _rows(root, max_files=max_files, max_bytes=max_bytes)
    second = _rows(root, max_files=max_files, max_bytes=max_bytes)
    if first != second:
        raise ScanError("subset changed between scans")
    material = json.dumps(first, separators=(",", ":"), ensure_ascii=True).encode()
    return {
        "entry_count": len(first),
        "total_size": sum(row[1] for row in first),
        "manifest_sha256": hashlib.sha256(material).hexdigest(),
        "scan_consistent": True,
        "captured_epoch": int(time.time()),
        "claim": "observation-only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        result = scan(args.root)
    except (OSError, ScanError) as exc:
        raise SystemExit(f"subset scan failed: {type(exc).__name__}") from None
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
