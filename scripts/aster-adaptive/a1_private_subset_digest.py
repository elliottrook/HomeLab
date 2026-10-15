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
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise ScanError("safe descriptor scan is unavailable")
    rows: list[tuple[str, int, str]] = []
    total = 0
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC
    pending = [(os.open(root, directory_flags), Path())]
    try:
        while pending:
            directory_fd, relative_dir = pending.pop()
            try:
                with os.scandir(directory_fd) as entries:
                    for entry in entries:
                        before = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
                        relative = relative_dir / entry.name
                        if stat.S_ISDIR(before.st_mode):
                            child_fd = os.open(entry.name, directory_flags, dir_fd=directory_fd)
                            child = os.fstat(child_fd)
                            if (child.st_dev, child.st_ino) != (before.st_dev, before.st_ino):
                                os.close(child_fd)
                                raise ScanError("subset directory changed during scan")
                            pending.append((child_fd, relative))
                            continue
                        if not stat.S_ISREG(before.st_mode):
                            raise ScanError("subset contains a non-regular entry")
                        size = before.st_size
                        if size < 0 or len(rows) >= max_files or total + size > max_bytes:
                            raise ScanError("subset exceeds fixed scan bounds")
                        digest = hashlib.sha256()
                        file_fd = os.open(entry.name, file_flags, dir_fd=directory_fd)
                        with os.fdopen(file_fd, "rb") as stream:
                            opened = os.fstat(stream.fileno())
                            if (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_size) != (
                                before.st_dev, before.st_ino, before.st_mode, size
                            ):
                                raise ScanError("subset file changed before read")
                            while chunk := stream.read(1024 * 1024):
                                digest.update(chunk)
                            after = os.fstat(stream.fileno())
                            if (after.st_size, after.st_mtime_ns, after.st_ctime_ns) != (
                                opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns
                            ):
                                raise ScanError("subset file changed during read")
                        rows.append((relative.as_posix(), size, digest.hexdigest()))
                        total += size
            finally:
                os.close(directory_fd)
    finally:
        for directory_fd, _ in pending:
            os.close(directory_fd)
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
