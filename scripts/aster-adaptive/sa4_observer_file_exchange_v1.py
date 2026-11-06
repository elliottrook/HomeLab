"""Fixed LXC side of the SA4 observer proof file exchange."""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import time
from typing import Callable

import sa4_observer_signer_v1 as observer


EXCHANGE_DIR = Path("/run/aster-sa4-observer-exchange")
EXPECTED_UID = 0
TIMEOUT_SECONDS = 60
SIGNATURE = re.compile(rb"[0-9a-f]{512}\n")


def _directory() -> None:
    metadata = EXCHANGE_DIR.lstat()
    if (not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != EXPECTED_UID
            or stat.S_IMODE(metadata.st_mode) != 0o700):
        raise ValueError("SA4 observer exchange directory changed")


def _write_exclusive(path: Path, raw: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if os.write(descriptor, raw) != len(raw):
            raise OSError("short SA4 observer exchange write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_signature(path: Path) -> str:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        metadata = os.fstat(descriptor)
        raw = os.read(descriptor, 514)
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != EXPECTED_UID
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_nlink != 1 or not SIGNATURE.fullmatch(raw)):
            raise ValueError("SA4 observer exchange response changed")
        return raw[:-1].decode("ascii")
    finally:
        os.close(descriptor)


def request_signature(statement: bytes, sequence: int, *,
                      monotonic: Callable[[], float] = time.monotonic,
                      sleep: Callable[[float], None] = time.sleep) -> str:
    if type(sequence) is not int or sequence not in (1, 2):
        raise ValueError("SA4 observer exchange sequence changed")
    observer.validate_statement(statement)
    _directory()
    request = EXCHANGE_DIR / f"request-{sequence}.json"
    response = EXCHANGE_DIR / f"response-{sequence}.signature"
    _write_exclusive(request, statement)
    deadline = monotonic() + TIMEOUT_SECONDS
    while monotonic() < deadline:
        try:
            signature = _read_signature(response)
        except FileNotFoundError:
            sleep(0.1)
            continue
        return signature
    raise TimeoutError("SA4 observer exchange response timed out")
