"""Private, locked and atomic JSON persistence for podcast requests."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Callable, TypeVar


T = TypeVar("T")
MAX_STATE_BYTES = 4 * 1024 * 1024
EMPTY = {"schema": "aster-podcast-request-queue.v1", "candidates": {}, "requests": {},
         "idempotency": {}}


class PersistenceError(RuntimeError):
    pass


def _validate_root(root: Path) -> None:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or root.is_symlink() or info.st_mode & 0o077:
        raise PersistenceError("state-root-custody")


def _load(path: Path) -> dict:
    if not path.exists():
        return json.loads(json.dumps(EMPTY))
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_nlink != 1
            or info.st_mode & 0o077 or info.st_size > MAX_STATE_BYTES):
        raise PersistenceError("state-file-custody")
    value = json.loads(path.read_text())
    if (not isinstance(value, dict) or set(value) != set(EMPTY)
            or value.get("schema") != EMPTY["schema"]
            or any(not isinstance(value[name], dict)
                   for name in ("candidates", "requests", "idempotency"))):
        raise PersistenceError("state-schema")
    return value


def _write(path: Path, value: dict) -> None:
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if len(encoded) > MAX_STATE_BYTES:
        raise PersistenceError("state-size")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".state.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
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


class QueueStore:
    def __init__(self, root: Path):
        self.root = root
        self.state = root / "state.json"
        self.lock = root / "state.lock"

    def transact(self, operation: Callable[[dict], T], *, write: bool) -> T:
        _validate_root(self.root)
        flags = os.O_CREAT | os.O_RDWR | os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.lock, flags, 0o600)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise PersistenceError("lock-custody")
            os.fchmod(descriptor, 0o600)
            fcntl.flock(descriptor, fcntl.LOCK_EX if write else fcntl.LOCK_SH)
            value = _load(self.state)
            result = operation(value)
            if write:
                _write(self.state, value)
            return result
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
