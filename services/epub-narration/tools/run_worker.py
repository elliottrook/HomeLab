#!/usr/bin/env python3
"""Run one bounded compiler attempt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import time

from epub_narration.worker import WorkerConfig, run_once


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--cleanup", type=Path, required=True)
    parser.add_argument("--max-runtime-seconds", type=int, default=0)
    args = parser.parse_args()
    if args.max_runtime_seconds < 0:
        parser.error("--max-runtime-seconds must be non-negative")
    stopping = False
    deadline = (
        time.monotonic() + args.max_runtime_seconds
        if args.max_runtime_seconds
        else None
    )

    def request_stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    result = run_once(WorkerConfig(
        database=args.database,
        library_root=args.library_root,
        data_root=args.data_root,
        model=args.model,
        voices=args.voices,
        cleanup=args.cleanup,
    ), should_stop=lambda: stopping or (deadline is not None and time.monotonic() >= deadline))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"healthy", "idle", "suspended"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
