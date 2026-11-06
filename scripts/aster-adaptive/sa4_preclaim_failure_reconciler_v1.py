"""Reconcile the exact SA4 v7 pre-claim checkpoint collision.

This owner is deliberately narrower than a general cleanup command.  It accepts
only the retained v4 attempt, proves that no checkpoint, claim, repair, observer
request or evidence write from that attempt occurred, records one durable
content-free receipt, and then releases only the matching runtime controls.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import time

import sa4_distinct_registry_bindings_v2 as bindings
import sa4_single_file_repair_contract_v1 as contract


PLAN_ID = "sa4-canary-v2-first-repair-v1"
PLAN_SHA256 = "e708b2f76cbca8d859ae3bae188ed47d37036949efb3347fdaf00eb5390a647b"
GRANT_ID = "sa4-canary-v2-third-grant-v1-20261106"
TARGET_SHA256 = "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0"
TARGET_PATH = Path("/var/lib/aster/sa4/canary-adapter-v2.json")
INPUT_DIR = Path("/var/lib/aster/sa4/transaction-input-v4")
EVIDENCE_DIR = Path("/var/lib/aster/sa4/transaction-evidence-v4")
LEDGER_RECORD = Path(
    "/var/lib/aster/sa4/one-use-ledger-v4/records/"
    "sa4-canary-v2-third-grant-v1-20261106.json")
CHECKPOINT_PATH = Path(
    "/var/lib/aster/sa4/checkpoints/"
    "sa4-canary-v2-first-repair-v1.original")
CHECKPOINT_TEMP = Path(
    "/var/lib/aster/sa4/checkpoints/"
    ".sa4-canary-v2-first-repair-v1.checkpoint.tmp")
EXCHANGE_DIR = Path("/run/aster-sa4-observer-exchange")
LOCK_PATH = Path("/run/aster-sa4-operation.lock")
STOP_PATH = Path("/run/aster-sa4-emergency-stop")
RECEIPT_PATH = EVIDENCE_DIR / "preclaim-reconciliation.json"
EXPECTED_UID = 0
EXPECTED_GID = 0


def _read_regular(path: Path, *, mode: int, maximum: int = 65536) -> tuple[bytes, os.stat_result]:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        metadata = os.fstat(descriptor)
        raw = os.read(descriptor, maximum + 1)
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != EXPECTED_UID
                or metadata.st_gid != EXPECTED_GID or metadata.st_nlink != 1
                or stat.S_IMODE(metadata.st_mode) != mode
                or not 1 <= len(raw) <= maximum or os.read(descriptor, 1)):
            raise ValueError("SA4 preclaim reconciliation custody changed")
        return raw, metadata
    finally:
        os.close(descriptor)


def _unique_json(raw: bytes) -> dict[str, object]:
    pairs = json.loads(raw.decode("utf-8"), object_pairs_hook=lambda value: value)
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("SA4 preclaim reconciliation JSON is ambiguous")
        value[key] = item
    if raw != contract.canonical(value):
        raise ValueError("SA4 preclaim reconciliation JSON is not canonical")
    return value


def _directory(path: Path, *, empty: bool = False) -> None:
    metadata = path.lstat()
    if (not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != EXPECTED_UID or metadata.st_gid != EXPECTED_GID
            or stat.S_IMODE(metadata.st_mode) != 0o700):
        raise ValueError("SA4 preclaim reconciliation directory custody changed")
    if empty and any(path.iterdir()):
        raise ValueError("SA4 preclaim reconciliation expected an empty directory")


def _control(path: Path, expected: bytes) -> tuple[int, os.stat_result]:
    descriptor = os.open(path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    metadata = os.fstat(descriptor)
    path_metadata = path.lstat()
    if ((metadata.st_dev, metadata.st_ino) !=
            (path_metadata.st_dev, path_metadata.st_ino)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != EXPECTED_UID
            or metadata.st_gid != EXPECTED_GID or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600):
        os.close(descriptor)
        raise ValueError("SA4 preclaim runtime-control custody changed")
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    raw = os.read(descriptor, 4097)
    if raw != expected or os.read(descriptor, 1):
        os.close(descriptor)
        raise ValueError("SA4 preclaim runtime-control content changed")
    return descriptor, metadata


def reconcile(*, observed_epoch: int) -> bytes:
    if type(observed_epoch) is not int or observed_epoch < 1:
        raise ValueError("SA4 preclaim reconciliation time changed")
    _directory(INPUT_DIR)
    _directory(EVIDENCE_DIR, empty=True)
    _directory(EXCHANGE_DIR, empty=True)
    if CHECKPOINT_TEMP.exists() or RECEIPT_PATH.exists():
        raise ValueError("SA4 preclaim reconciliation path is not fresh")

    plan_raw, _ = _read_regular(INPUT_DIR / "plan", mode=0o600)
    with bindings.accepted_registry(plan_raw):
        plan = contract.validate_plan(plan_raw)
    if (hashlib.sha256(plan_raw).hexdigest() != PLAN_SHA256
            or plan["plan_id"] != PLAN_ID
            or plan["precondition"]["expected_sha256"] != TARGET_SHA256):
        raise ValueError("SA4 preclaim reconciliation plan changed")

    target_raw, target_stat = _read_regular(TARGET_PATH, mode=0o644, maximum=4096)
    checkpoint_raw, checkpoint_stat = _read_regular(
        CHECKPOINT_PATH, mode=0o600, maximum=4096)
    if (hashlib.sha256(target_raw).hexdigest() != TARGET_SHA256
            or checkpoint_raw != target_raw
            or target_stat.st_size != checkpoint_stat.st_size):
        raise ValueError("SA4 preclaim target or retained checkpoint changed")

    ledger_raw, _ = _read_regular(LEDGER_RECORD, mode=0o600, maximum=16384)
    ledger = _unique_json(ledger_raw)
    if (ledger.get("grant_id") != GRANT_ID
            or ledger.get("plan_sha256") != PLAN_SHA256
            or ledger.get("target_sha256") != TARGET_SHA256
            or ledger.get("state") != "ready" or ledger.get("use_count") != 0
            or ledger.get("effect_authorized") is not False
            or ledger.get("automatic_retry") is not False):
        raise ValueError("SA4 preclaim ledger state changed")

    expected_lock = contract.canonical({
        "schema": "aster-sa4-operation-lock.v1", "plan_id": PLAN_ID,
        "plan_sha256": PLAN_SHA256})
    expected_stop = contract.canonical({
        "schema": "aster-sa4-emergency-stop.v1", "plan_id": PLAN_ID,
        "plan_sha256": PLAN_SHA256, "state": "armed"})
    lock_fd = stop_fd = -1
    try:
        lock_fd, lock_stat = _control(LOCK_PATH, expected_lock)
        stop_fd, stop_stat = _control(STOP_PATH, expected_stop)
        receipt = contract.canonical({
            "schema": "aster-sa4-preclaim-failure-reconciliation.v1",
            "observed_epoch": observed_epoch,
            "plan_id": PLAN_ID, "plan_sha256": PLAN_SHA256,
            "grant_id": GRANT_ID, "ledger_state": "ready",
            "use_count": 0, "target_sha256": TARGET_SHA256,
            "retained_checkpoint_sha256": TARGET_SHA256,
            "failure_class": "CHECKPOINT_PATH_COLLISION",
            "checkpoint_created": False, "grant_claimed": False,
            "repair_effects": 0, "observer_requests": 0,
            "automatic_retry": False, "runtime_controls_released": True,
            "retained_evidence": True,
        })
        descriptor = os.open(
            RECEIPT_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            os.write(descriptor, receipt); os.fsync(descriptor)
        finally:
            os.close(descriptor)
        directory = os.open(EVIDENCE_DIR, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        for path, metadata in ((STOP_PATH, stop_stat), (LOCK_PATH, lock_stat)):
            current = path.lstat()
            if (current.st_dev, current.st_ino) != (metadata.st_dev, metadata.st_ino):
                raise ValueError("SA4 preclaim runtime-control identity changed")
        STOP_PATH.unlink(); LOCK_PATH.unlink()
        return receipt
    finally:
        for descriptor in (stop_fd, lock_fd):
            if descriptor >= 0:
                os.close(descriptor)


def main(arguments: list[str]) -> int:
    if arguments:
        raise ValueError("SA4 preclaim reconciler accepts no arguments")
    os.write(1, reconcile(observed_epoch=int(time.time())))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(os.sys.argv[1:]))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=os.sys.stderr)
        raise SystemExit(1)
