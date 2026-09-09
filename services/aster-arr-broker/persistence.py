"""Atomic, locked persistence for the narrow ARR broker state."""

from __future__ import annotations

import fcntl
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


MAX_AUDIT_BYTES = 8 * 1024 * 1024


@contextmanager
def state_lock(path: Path, *, owner: tuple[int, int] | None = None) -> Iterator[None]:
    """Hold the broker's single cross-process transaction lock."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_RDWR | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    locked = False
    try:
        status = os.fstat(descriptor)
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            raise OSError("broker lock is not a private regular file")
        os.fchmod(descriptor, 0o600)
        if owner is not None:
            os.fchown(descriptor, *owner)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        locked = True
        yield
    finally:
        if locked:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def atomic_json_write(
    path: Path,
    payload: object,
    *,
    mode: int = 0o600,
    owner: tuple[int, int] | None = None,
) -> None:
    """Replace one JSON file durably without following a temporary symlink."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        if owner is not None:
            os.fchown(descriptor, *owner)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def append_json_line(path: Path, payload: object) -> None:
    """Append one already-bounded audit object and force it to stable storage."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY | os.O_CLOEXEC | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        status = os.fstat(descriptor)
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_nlink != 1
            or status.st_size > MAX_AUDIT_BYTES
        ):
            raise OSError("audit path is not a bounded private regular file")
        os.fchmod(descriptor, 0o600)
        rendered = (json.dumps(payload, separators=(",", ":")) + "\n").encode()
        if status.st_size + len(rendered) > MAX_AUDIT_BYTES:
            raise OSError("audit file reached its size limit")
        view = memoryview(rendered)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("audit append did not make progress")
            view = view[written:]
        os.fsync(descriptor)
        directory = os.open(path.parent, os.O_RDONLY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.close(descriptor)
