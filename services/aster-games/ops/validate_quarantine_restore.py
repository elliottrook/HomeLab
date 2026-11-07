#!/usr/bin/env python3
"""Prove ROMarr duplicate quarantine/restore with the synthetic fixture only."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import time
from urllib.request import Request, urlopen


BASE = os.environ.get("ROMARR_URL", "http://192.168.20.38:6868").rstrip("/")
API_KEY = os.environ.get("ROMARR_API_KEY", "")
LIBRARY = Path("/srv/aster-games/library/nes")
ORIGINAL = LIBRARY / "Aster Infrastructure Test (World) (Homebrew).nes"
DUPLICATE = LIBRARY / "Aster Infrastructure Test Duplicate (Homebrew).nes"


def request(path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    call = Request(
        BASE + path,
        data=data,
        method="GET" if data is None else "POST",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Api-Key": API_KEY,
        },
    )
    with urlopen(call, timeout=30) as response:
        return json.load(response)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    started = request("/api/v1/audit", {"platform": "nes"})
    if started.get("error"):
        raise RuntimeError("audit did not start")
    state = started
    for _ in range(30):
        if state.get("status") in {"done", "failed"}:
            break
        time.sleep(1)
        state = request("/api/v1/audit")
    if state.get("status") != "done":
        raise RuntimeError("audit did not complete")
    return state


def main() -> int:
    if len(API_KEY) < 20 or not ORIGINAL.is_file() or DUPLICATE.exists():
        raise RuntimeError("fixture or validation precondition failed")
    shutil.copy2(ORIGINAL, DUPLICATE)
    try:
        before = audit()
        duplicates = before.get("duplicates", [])
        if len(duplicates) != 1 or duplicates[0].get("file") != "nes/" + DUPLICATE.name:
            raise RuntimeError("audit did not identify the bounded duplicate")
        moved = request(
            "/api/v1/audit/quarantine/move",
            {"platform": "nes", "files": duplicates},
        )
        entries = moved.get("entries", [])
        if not moved.get("ok") or len(entries) != 1 or DUPLICATE.exists():
            raise RuntimeError("quarantine move failed")
        restored = request(
            "/api/v1/audit/restore",
            {"manifest_id": moved.get("manifest_id"), "entry_id": entries[0].get("id")},
        )
        if not restored.get("ok") or not DUPLICATE.is_file():
            raise RuntimeError("quarantine restore failed")
        identical = digest(ORIGINAL) == digest(DUPLICATE)
        if not identical:
            raise RuntimeError("restored duplicate hash mismatch")
        manifest_id = str(moved.get("manifest_id") or "")
    finally:
        DUPLICATE.unlink(missing_ok=True)
    after = audit()
    result = {
        "before_scanned": int(before.get("scanned") or 0),
        "before_verified": int(before.get("verified") or 0),
        "duplicates_found": len(duplicates),
        "quarantine_manifest_recorded": bool(manifest_id),
        "restore_hash_identical": identical,
        "test_duplicate_removed": not DUPLICATE.exists(),
        "after_scanned": int(after.get("scanned") or 0),
        "after_duplicates": len(after.get("duplicates", [])),
    }
    result["ok"] = (
        result["before_scanned"] == 2
        and result["before_verified"] == 2
        and result["duplicates_found"] == 1
        and result["quarantine_manifest_recorded"]
        and result["restore_hash_identical"]
        and result["test_duplicate_removed"]
        and result["after_scanned"] == 1
        and result["after_duplicates"] == 0
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
