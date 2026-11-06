"""Fixed LXC side of the SA4 observer proof file exchange."""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import time
import json
from typing import Callable

EXCHANGE_DIR = Path("/run/aster-sa4-observer-exchange")
EXPECTED_UID = 0
TIMEOUT_SECONDS = 60
SIGNATURE = re.compile(rb"[0-9a-f]{512}\n")
OBSERVER_ID = "aster-observer"
KEY_SHA256 = "a8b5e876898ddcd7882a51c74d8b8388bb26160c96f87ab23dbeeecab9c0892b"
FIELDS = {"schema", "receipt_sha256", "observer_id",
          "observer_key_sha256", "signature_algorithm", "authority"}

def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()

def validate_statement(raw: bytes) -> bytes:
    try: value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("SA4 observer statement is not JSON") from exc
    digest = value.get("receipt_sha256") if isinstance(value, dict) else None
    if (not isinstance(value, dict) or set(value) != FIELDS
            or value["schema"] != "aster-sa4-independent-receipt-proof.v1"
            or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or value["observer_id"] != OBSERVER_ID
            or value["observer_key_sha256"] != KEY_SHA256
            or value["signature_algorithm"] != "rsa-pkcs1v1_5-sha256"
            or value["authority"] != "observer-proof-only-no-effect"
            or canonical(value) != raw):
        raise ValueError("SA4 observer statement changed")
    return raw


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
    validate_statement(statement)
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
