#!/usr/bin/env python3
"""One-shot, read-only timing observation for the fixed 104/110/116 archives.

This is source-only. It is not installed, scheduled, or an admission receipt.
The fixed producer supplies all backup/task/source/deadline checks; its save
callback is replaced with a no-op so a passing scan cannot write a receipt.
"""

from __future__ import annotations

import json
import os
import time

from retained_archive_integrity import RECEIPT_PATH
from retained_archive_producer_candidate import _runner, produce


def observe(*, runner=_runner, clock=lambda: int(time.time())) -> dict:
    if os.geteuid() != 0:
        raise PermissionError("archive observation requires root")
    root = RECEIPT_PATH.parent
    conflicting_state = (
        root / "lease.json",
        root / "lease.lock",
        root / "application-b60" / "application-b60.json",
        root / "application-b60" / "application-b60.lock",
    )
    if any(os.path.lexists(path) for path in conflicting_state):
        raise RuntimeError("conflicting lease state or lock exists")
    receipt = produce(runner, clock=clock, save=lambda _receipt: None)
    return {
        "schema": "aster-read-only-archive-timing.v1",
        "state": "complete",
        "date": receipt["date"],
        "archives": [
            {key: row[key] for key in (
                "vmid", "volid", "size", "ctime", "test_started_epoch",
                "test_finished_epoch", "test_elapsed_ms", "test_exit",
            )}
            for row in receipt["archives"]
        ],
        "admission_receipt_written": False,
    }


def main() -> int:
    try:
        result = observe()
    except Exception as exc:
        # Do not print fixed-source command output, file paths or private data.
        print(json.dumps({"schema": "aster-read-only-archive-timing.v1",
                          "state": "no_go", "error_class": type(exc).__name__},
                         sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
