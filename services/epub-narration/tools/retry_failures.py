#!/usr/bin/env python3
"""Requeue one bounded failure class without exposing source identifiers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from epub_narration import COMPILER_CONTRACT
from epub_narration.state import FAILURE_CODES, QueueStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--failure-code", choices=sorted(FAILURE_CODES), required=True)
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()
    store = QueueStore(args.state_root / "queue.db")
    store.initialize()
    retried = store.retry_failed(
        COMPILER_CONTRACT,
        args.failure_code,
        args.max_attempts,
    )
    print(json.dumps({"retried": retried}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
