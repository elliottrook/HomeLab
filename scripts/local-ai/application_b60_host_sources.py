"""Offline candidate for fixed root-owned A1 pre-lease source adapters."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

MAX_SOURCE_BYTES = 16_000


class HostSourceError(ValueError):
    pass


@dataclass(frozen=True)
class AttestedSource:
    source: str
    cycle: str
    observed_epoch: int
    payload: dict[str, object]
    payload_sha256: str
    verified: bool = True


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode("utf-8")


def read_attested_source(path: Path, *, expected_source: str,
                         expected_cycle: str, expected_digest: str,
                         now_epoch: int) -> AttestedSource:
    """Read one pinned source envelope without contacting any system."""
    if path.is_symlink():
        raise HostSourceError("source path is a symlink")
    try:
        parent = path.parent.lstat()
        info = path.lstat()
    except FileNotFoundError as exc:
        raise HostSourceError("source file is absent") from exc
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise HostSourceError("source parent custody failed")
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
            or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
            or info.st_size > MAX_SOURCE_BYTES):
        raise HostSourceError("source file custody failed")
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HostSourceError("source envelope is unreadable") from exc
    if (not isinstance(value, dict)
            or set(value) != {"schema", "source", "cycle", "observed_epoch",
                               "payload", "payload_sha256"}
            or value["schema"] != "aster-source-observation.v1"
            or value["source"] != expected_source
            or value["cycle"] != expected_cycle
            or type(value["observed_epoch"]) is not int
            or value["observed_epoch"] > now_epoch
            or not isinstance(value["payload"], dict)
            or type(value["payload_sha256"]) is not str
            or len(value["payload_sha256"]) != 64):
        raise HostSourceError("source envelope shape is invalid")
    actual = hashlib.sha256(_canonical(value["payload"])).hexdigest()
    if actual != value["payload_sha256"] or actual != expected_digest:
        raise HostSourceError("source payload digest is not pinned")
    return AttestedSource(source=value["source"], cycle=value["cycle"],
                          observed_epoch=value["observed_epoch"],
                          payload=value["payload"],
                          payload_sha256=actual)
