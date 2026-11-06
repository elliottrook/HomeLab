"""Conservative per-file snapshot coverage before predicting pool reclaim."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReclaimEstimate:
    bytes: int
    reason: str | None


def snapshot_names(dataset: str = "Media/data") -> tuple[str, ...]:
    """List direct dataset snapshots; never change snapshot retention here."""
    if dataset != "Media/data":
        raise ValueError("unexpected media dataset")
    result = subprocess.run(
        ["zfs", "list", "-H", "-t", "snapshot", "-o", "name", "-r", dataset],
        capture_output=True, text=True, timeout=30, check=True,
    )
    names = []
    for line in result.stdout.splitlines():
        if line.startswith(dataset + "@"):
            name = line[len(dataset) + 1:]
            if not name or "/" in name or ".." in name:
                raise RuntimeError("invalid snapshot name")
            names.append(name)
    return tuple(names)


def estimate_unprotected_file(
    path: Path, *, data_root: Path, snapshots: tuple[str, ...],
) -> ReclaimEstimate:
    """Hold files visible in any retained snapshot or sharing an inode.

    A positive number is an optimistic file-size bound, not guaranteed ZFS
    allocation. The controller must measure actual pool allocation afterward.
    """
    root = data_root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or not path.is_file():
        return ReclaimEstimate(0, "file outside data root or missing")
    info = path.stat()
    if info.st_nlink != 1 or info.st_size <= 0:
        return ReclaimEstimate(0, "shared or empty file")
    relative = resolved.relative_to(root)
    for name in snapshots:
        if not name or "/" in name or ".." in name:
            return ReclaimEstimate(0, "snapshot inventory invalid")
        if (data_root / ".zfs" / "snapshot" / name / relative).exists():
            return ReclaimEstimate(0, "file retained by snapshot")
    return ReclaimEstimate(info.st_size, None)
