"""Reconcile the exact v8 pre-owner failure caused by an empty exchange dir."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import time

import sa4_distinct_registry_bindings_v2 as bindings
import sa4_single_file_repair_contract_v1 as contract


PLAN_ID = "sa4-canary-v2-second-repair-v1"
PLAN_SHA256 = "1fa2e58eebb4ec533079be28ee211a25df444ead2dcfcae0f1622b5c77e18746"
GRANT_ID = "sa4-canary-v2-fourth-grant-v1-20261106"
TARGET_SHA256 = "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0"
INPUT_DIR = Path("/var/lib/aster/sa4/transaction-input-v5")
EVIDENCE_DIR = Path("/var/lib/aster/sa4/transaction-evidence-v5")
LEDGER_RECORD = Path(
    "/var/lib/aster/sa4/one-use-ledger-v5/records/"
    "sa4-canary-v2-fourth-grant-v1-20261106.json")
TARGET_PATH = Path("/var/lib/aster/sa4/canary-adapter-v2.json")
CHECKPOINT_PATH = Path(
    "/var/lib/aster/sa4/checkpoints/"
    "sa4-canary-v2-second-repair-v1.original")
EXCHANGE_DIR = Path("/run/aster-sa4-observer-exchange")
LOCK_PATH = Path("/run/aster-sa4-operation.lock")
STOP_PATH = Path("/run/aster-sa4-emergency-stop")
RECEIPT_PATH = EVIDENCE_DIR / "preexchange-reconciliation.json"
EXPECTED_UID = 0
EXPECTED_GID = 0


def _directory(path: Path, *, empty: bool = False) -> os.stat_result:
    data = path.lstat()
    if (not stat.S_ISDIR(data.st_mode) or stat.S_ISLNK(data.st_mode)
            or data.st_uid != EXPECTED_UID or data.st_gid != EXPECTED_GID
            or stat.S_IMODE(data.st_mode) != 0o700):
        raise ValueError("SA4 preexchange directory custody changed")
    if empty and any(path.iterdir()):
        raise ValueError("SA4 preexchange directory is not empty")
    return data


def _read(path: Path, mode: int, maximum: int = 65536) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        data = os.fstat(descriptor); raw = os.read(descriptor, maximum + 1)
        if (not stat.S_ISREG(data.st_mode) or data.st_uid != EXPECTED_UID
                or data.st_gid != EXPECTED_GID or data.st_nlink != 1
                or stat.S_IMODE(data.st_mode) != mode
                or not 1 <= len(raw) <= maximum or os.read(descriptor, 1)):
            raise ValueError("SA4 preexchange file custody changed")
        return raw
    finally:
        os.close(descriptor)


def _json(raw: bytes) -> dict[str, object]:
    pairs = json.loads(raw.decode(), object_pairs_hook=lambda value: value)
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("SA4 preexchange JSON is ambiguous")
        value[key] = item
    if raw != contract.canonical(value):
        raise ValueError("SA4 preexchange JSON is not canonical")
    return value


def reconcile(*, observed_epoch: int) -> bytes:
    if type(observed_epoch) is not int or observed_epoch < 1:
        raise ValueError("SA4 preexchange time changed")
    _directory(INPUT_DIR); _directory(EVIDENCE_DIR, empty=True)
    exchange_stat = _directory(EXCHANGE_DIR, empty=True)
    if (LOCK_PATH.exists() or STOP_PATH.exists() or CHECKPOINT_PATH.exists()
            or RECEIPT_PATH.exists()):
        raise ValueError("SA4 preexchange effect state is not absent")
    plan_raw = _read(INPUT_DIR / "plan", 0o600)
    with bindings.accepted_registry(plan_raw):
        plan = contract.validate_plan(plan_raw)
    if (hashlib.sha256(plan_raw).hexdigest() != PLAN_SHA256
            or plan["plan_id"] != PLAN_ID):
        raise ValueError("SA4 preexchange plan changed")
    if hashlib.sha256(_read(TARGET_PATH, 0o644, 4096)).hexdigest() != TARGET_SHA256:
        raise ValueError("SA4 preexchange target changed")
    ledger = _json(_read(LEDGER_RECORD, 0o600, 16384))
    if (ledger.get("grant_id") != GRANT_ID
            or ledger.get("plan_sha256") != PLAN_SHA256
            or ledger.get("state") != "ready" or ledger.get("use_count") != 0
            or ledger.get("effect_authorized") is not False
            or ledger.get("automatic_retry") is not False):
        raise ValueError("SA4 preexchange ledger changed")
    current = EXCHANGE_DIR.lstat()
    if (current.st_dev, current.st_ino) != (exchange_stat.st_dev, exchange_stat.st_ino):
        raise ValueError("SA4 preexchange directory identity changed")
    EXCHANGE_DIR.rmdir()
    receipt = contract.canonical({
        "schema": "aster-sa4-preexchange-failure-reconciliation.v1",
        "observed_epoch": observed_epoch, "plan_id": PLAN_ID,
        "plan_sha256": PLAN_SHA256, "grant_id": GRANT_ID,
        "failure_class": "EXCHANGE_DIRECTORY_PREEXISTED_EMPTY",
        "ledger_state": "ready", "use_count": 0,
        "checkpoint_created": False, "grant_claimed": False,
        "repair_effects": 0, "observer_requests": 0,
        "target_sha256": TARGET_SHA256, "runtime_exchange_removed": True,
        "automatic_retry": False, "retained_evidence": True,
    })
    descriptor = os.open(RECEIPT_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        os.write(descriptor, receipt); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return receipt


def main(arguments: list[str]) -> int:
    if arguments:
        raise ValueError("SA4 preexchange reconciler accepts no arguments")
    os.write(1, reconcile(observed_epoch=int(time.time())))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(os.sys.argv[1:]))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=os.sys.stderr); raise SystemExit(1)
