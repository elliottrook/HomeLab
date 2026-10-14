"""Fixed TrueNAS producer for the content-free Mac pull receipt.

Install this file only behind the separately authorized root-owned wrapper.
It emits aggregate metadata and a digest, never filenames or file contents.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path("/mnt/Recovery/configuration/mac")
TASK_ID = 2
CHUNK = 1024 * 1024


def _task_finished() -> int:
    raw = subprocess.check_output(("midclt", "call", "rsynctask.query"), text=True)
    tasks = json.loads(raw)
    task = next((item for item in tasks if item.get("id") == TASK_ID), None)
    job = task.get("job", {}) if task else {}
    finished = job.get("time_finished", {}).get("$date")
    if not task or not task.get("enabled") or job.get("state") != "SUCCESS" or job.get("arguments") != [TASK_ID] or not isinstance(finished, int):
        raise RuntimeError("fixed Mac pull task is not a successful task-2 run")
    return finished // 1000


def build_receipt() -> dict[str, object]:
    finished = _task_finished()
    if not ROOT.is_dir() or ROOT.is_symlink():
        raise RuntimeError("fixed Mac pull root is unavailable")
    digest = hashlib.sha256()
    entry_count = 0
    total_size = 0
    latest_mtime = 0
    for directory, dirs, files in os.walk(ROOT, followlinks=False):
        dirs[:] = sorted(name for name in dirs if not (Path(directory) / name).is_symlink())
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                continue
            relative = path.relative_to(ROOT).as_posix().encode()
            stat = path.stat()
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            digest.update(stat.st_size.to_bytes(8, "big"))
            digest.update(stat.st_mtime_ns.to_bytes(8, "big", signed=False))
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(CHUNK), b""):
                    digest.update(chunk)
            entry_count += 1
            total_size += stat.st_size
            latest_mtime = max(latest_mtime, stat.st_mtime_ns // 1_000_000_000)
    if entry_count == 0 or total_size == 0:
        raise RuntimeError("fixed Mac pull root is empty")
    return {
        "schema": "mac-pull-summary-v1",
        "path": str(ROOT) + "/",
        "date": time.strftime("%Y_%m_%d", time.localtime(finished)),
        "entry_count": entry_count,
        "total_size": total_size,
        "latest_mtime": latest_mtime,
        "task_id": TASK_ID,
        "task_finished_epoch": finished,
        "captured_epoch": int(time.time()),
        "tree_sha256": digest.hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(build_receipt(), separators=(",", ":"), sort_keys=True))
