"""Hash-bound atomic helper for the temporary llama.cpp test key."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path


def _atomic(path: Path, payload: bytes, mode: int, uid: int, gid: int) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        os.fchown(fd, uid, gid)
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def append_key(path: Path, checkpoint: Path, key: bytes, *, uid: int | None = None, gid: int | None = None) -> str:
    if not 32 <= len(key) <= 256 or b"\n" in key or any(not 33 <= value <= 126 for value in key):
        raise ValueError("invalid test key")
    original = path.read_bytes()
    metadata = path.stat()
    owner = (metadata.st_uid, metadata.st_gid, metadata.st_mode & 0o777)
    if key + b"\n" in original.splitlines(keepends=True):
        raise ValueError("test key already present")
    if checkpoint.exists():
        checkpoint_metadata = checkpoint.stat()
        if (checkpoint.read_bytes(), checkpoint_metadata.st_uid, checkpoint_metadata.st_gid,
                checkpoint_metadata.st_mode & 0o777) != (original, *owner):
            raise ValueError("immutable pre-add checkpoint does not match source")
    else:
        _atomic(checkpoint, original, owner[2], owner[0], owner[1])
    payload = original if original.endswith(b"\n") else original + b"\n"
    payload += key + b"\n"
    _atomic(path, payload, owner[2], owner[0], owner[1])
    return hashlib.sha256(key).hexdigest()


def remove_key_hash(path: Path, checkpoint: Path, key_sha256: str, *, uid: int | None = None, gid: int | None = None) -> None:
    if len(key_sha256) != 64 or any(value not in "0123456789abcdef" for value in key_sha256):
        raise ValueError("invalid key hash")
    if not checkpoint.exists():
        raise ValueError("immutable pre-add checkpoint is missing")
    metadata = path.stat()
    owner = (metadata.st_uid, metadata.st_gid, metadata.st_mode & 0o777)
    original = checkpoint.read_bytes()
    checkpoint_metadata = checkpoint.stat()
    if (checkpoint_metadata.st_uid, checkpoint_metadata.st_gid,
            checkpoint_metadata.st_mode & 0o777) != owner:
        raise ValueError("checkpoint metadata does not match key file")
    current_bytes = path.read_bytes()
    if current_bytes == original:
        return
    current = current_bytes.splitlines(keepends=True)
    matches = [line for line in current if hashlib.sha256(line.rstrip(b"\r\n")).hexdigest() == key_sha256]
    if len(matches) != 1:
        raise ValueError("expected exactly one temporary key")
    removed = matches[0].rstrip(b"\r\n")
    expected_current = original + (b"" if original.endswith(b"\n") else b"\n") + removed + b"\n"
    if current_bytes != expected_current:
        raise ValueError("key file drifted from immutable pre-add checkpoint")
    _atomic(path, original, owner[2], owner[0], owner[1])
