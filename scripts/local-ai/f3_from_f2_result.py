#!/usr/bin/env python3
"""Build one retained F3 receipt from a successful fixed-cycle F2 result.

The conversion performs no archive scan. It accepts only the fixed current-day
F2 state, re-resolves and re-stats all three unchanged archives, validates the
result with the retained-receipt verifier, then creates the fixed receipt once.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from backup_receipt_adapter import verify_proxmox_artifacts
from f2_scheduled_release_candidate import LOCAL_ZONE, SCHEMA as F2_SCHEMA, _validate_projection
from retained_archive_integrity import (
    ARCHIVE_FIELDS, FIELDS, IntegrityError, RECEIPT_PATH, SCHEMA,
    fixed_proxmox_inventory, fixed_resolve, verify,
)

F2_STATE_ROOT = Path("/var/lib/local-ai-lab/f2-scheduled")
MAX_STATE_BYTES = 16 * 1024
MAX_F2_AGE_SECONDS = 3 * 60 * 60


class F3ConversionError(ValueError):
    pass


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise F3ConversionError("F2 state contains duplicate keys")
        value[key] = item
    return value


def canonical_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def secure_read(path: Path, *, required_uid: int = 0) -> tuple[dict, bytes]:
    parent = path.parent.stat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != required_uid
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise F3ConversionError("F2 state parent custody differs")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise F3ConversionError("F2 state cannot be opened safely") from exc
    try:
        info = os.fstat(descriptor)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != required_uid
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                or not 0 < info.st_size <= MAX_STATE_BYTES):
            raise F3ConversionError("F2 state custody or size differs")
        raw = os.read(descriptor, MAX_STATE_BYTES + 1)
    finally:
        os.close(descriptor)
    if len(raw) > MAX_STATE_BYTES:
        raise F3ConversionError("F2 state is oversized")
    try:
        value = json.loads(raw, object_pairs_hook=_unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise F3ConversionError("F2 state JSON is invalid") from exc
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise F3ConversionError("F2 state is not canonical JSON")
    return value, raw


def _identity(path: str, lstat: Callable[[str], os.stat_result]) -> dict[str, int]:
    info = lstat(path)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise F3ConversionError("archive identity is not a single regular file")
    return {
        "device": info.st_dev, "inode": info.st_ino,
        "mtime_ns": info.st_mtime_ns, "ctime_ns": info.st_ctime_ns,
        "size": info.st_size,
    }


def build_receipt(state: dict, *, cycle: str, now_epoch: int,
                  inventory: list[dict], resolve: Callable[[str], str],
                  lstat: Callable[[str], os.stat_result]) -> dict:
    expected = {"schema", "cycle", "phase", "state", "error_class",
                "first_failure_phase", "failure_class", "result"}
    if (set(state) != expected or state.get("schema") != F2_SCHEMA
            or state.get("cycle") != cycle or state.get("phase") != "final"
            or state.get("state") != "complete" or state.get("error_class") != ""
            or state.get("first_failure_phase") != "" or state.get("failure_class") != ""):
        raise F3ConversionError("F2 terminal state is not an exact success")
    projection = state["result"]
    try:
        _validate_projection(projection, cycle)
        artifacts = verify_proxmox_artifacts(inventory, date_prefix=cycle.replace("-", "_"))
    except Exception as exc:
        raise F3ConversionError("F2 projection or current inventory is invalid") from exc
    rows = projection["archives"]
    if now_epoch - max(row["test_finished_epoch"] for row in rows) > MAX_F2_AGE_SECONDS:
        raise F3ConversionError("F2 result is too old for F3 conversion")
    converted = []
    for artifact, row in zip(artifacts, rows):
        if (row["vmid"] != artifact.vmid or row["volid"] != artifact.volid
                or row["size"] != artifact.size or row["ctime"] != artifact.ctime):
            raise F3ConversionError("F2 row no longer matches current inventory")
        path = resolve(artifact.volid)
        identity = _identity(path, lstat)
        if identity["size"] != artifact.size:
            raise F3ConversionError("archive size changed after F2")
        converted.append({
            "vmid": artifact.vmid, "volid": artifact.volid,
            "size": artifact.size, "ctime": artifact.ctime, "path": path,
            **{key: identity[key] for key in ("device", "inode", "mtime_ns", "ctime_ns")},
            "test_started_epoch": row["test_started_epoch"],
            "test_finished_epoch": row["test_finished_epoch"],
            "test_elapsed_ms": row["test_elapsed_ms"], "test_exit": 0,
        })
    receipt = {
        "schema": SCHEMA, "date": cycle.replace("-", "_"),
        "started_epoch": min(row["test_started_epoch"] for row in rows),
        "finished_epoch": max(row["test_finished_epoch"] for row in rows),
        "archives": converted,
    }
    if set(receipt) != FIELDS or any(set(row) != ARCHIVE_FIELDS for row in converted):
        raise F3ConversionError("constructed F3 schema differs")
    try:
        verify(receipt, inventory, date=receipt["date"], now_epoch=now_epoch,
               resolve=resolve, lstat=lstat, max_age_seconds=MAX_F2_AGE_SECONDS)
    except IntegrityError as exc:
        raise F3ConversionError("constructed F3 receipt does not verify") from exc
    return receipt


def write_once(path: Path, value: dict, *, required_uid: int = 0) -> str:
    if os.geteuid() != required_uid:
        raise F3ConversionError("root identity is required")
    parent = path.parent.stat()
    if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != required_uid
            or stat.S_IMODE(parent.st_mode) != 0o700):
        raise F3ConversionError("F3 receipt parent custody differs")
    if os.path.lexists(path):
        raise F3ConversionError("F3 receipt already exists")
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    if len(raw) > 8192:
        raise F3ConversionError("F3 receipt is oversized")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        os.unlink(temporary)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return hashlib.sha256(raw).hexdigest()


def produce(*, clock: Callable[[], int] = lambda: int(time.time()),
            inventory=fixed_proxmox_inventory, resolve=fixed_resolve,
            lstat=os.lstat, target: Path = RECEIPT_PATH,
            required_uid: int = 0) -> tuple[dict, str]:
    now_epoch = clock()
    cycle = datetime.fromtimestamp(now_epoch, LOCAL_ZONE).strftime("%Y-%m-%d")
    state_path = F2_STATE_ROOT / f"{cycle}.json"
    state, original = secure_read(state_path, required_uid=required_uid)
    current_inventory = inventory()
    receipt = build_receipt(state, cycle=cycle, now_epoch=now_epoch,
                            inventory=current_inventory, resolve=resolve, lstat=lstat)
    _state_again, repeated = secure_read(state_path, required_uid=required_uid)
    if repeated != original:
        raise F3ConversionError("F2 state changed during conversion")
    digest = write_once(target, receipt, required_uid=required_uid)
    return receipt, digest


def main() -> int:
    try:
        receipt, digest = produce()
    except (F3ConversionError, IntegrityError, OSError, ValueError):
        print(json.dumps({"state": "no_go", "receipt_written": False}, sort_keys=True))
        return 1
    print(json.dumps({"state": "complete", "receipt_written": True,
                      "archives": len(receipt["archives"]),
                      "receipt_sha256": digest}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
