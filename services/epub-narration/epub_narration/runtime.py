"""Small private-runtime primitives shared by the monitor and worker."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import tempfile
import time


@contextmanager
def exclusive_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("worker-lock-held") from exc
        yield
    finally:
        os.close(descriptor)


def atomic_private_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}-", delete=False
    ) as handle:
        json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def status_payload(*, state: str, counts: dict[str, int], oldest_queued_age: float | None) -> dict:
    if state not in {"healthy", "idle", "failed", "disabled"}:
        raise ValueError("status-state")
    return {
        "schema": 1,
        "state": state,
        "updated_at": int(time.time()),
        "counts": dict(sorted(counts.items())),
        "oldest_queued_seconds": None if oldest_queued_age is None else int(oldest_queued_age),
    }
