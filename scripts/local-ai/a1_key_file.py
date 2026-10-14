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


def append_key(path: Path, checkpoint: Path, key: bytes, *, uid: int, gid: int) -> str:
    if not 32 <= len(key) <= 256 or b"\n" in key or any(not 33 <= value <= 126 for value in key):
        raise ValueError("invalid test key")
    original = path.read_bytes()
    if key + b"\n" in original.splitlines(keepends=True):
        raise ValueError("test key already present")
    _atomic(checkpoint, original, 0o600, uid, gid)
    payload = original if original.endswith(b"\n") else original + b"\n"
    payload += key + b"\n"
    _atomic(path, payload, 0o600, uid, gid)
    return hashlib.sha256(key).hexdigest()


def remove_key_hash(path: Path, checkpoint: Path, key_sha256: str, *, uid: int, gid: int) -> None:
    if len(key_sha256) != 64 or any(value not in "0123456789abcdef" for value in key_sha256):
        raise ValueError("invalid key hash")
    current = path.read_bytes().splitlines(keepends=True)
    matches = [line for line in current if hashlib.sha256(line.rstrip(b"\r\n")).hexdigest() == key_sha256]
    if len(matches) != 1:
        raise ValueError("expected exactly one temporary key")
    _atomic(checkpoint, path.read_bytes(), 0o600, uid, gid)
    _atomic(path, b"".join(line for line in current if line not in matches), 0o600, uid, gid)
