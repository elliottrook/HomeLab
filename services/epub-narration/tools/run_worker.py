#!/usr/bin/env python3
"""Run one bounded compiler attempt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from epub_narration.worker import WorkerConfig, run_once


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--cleanup", type=Path, required=True)
    args = parser.parse_args()
    result = run_once(WorkerConfig(
        database=args.database,
        library_root=args.library_root,
        data_root=args.data_root,
        model=args.model,
        voices=args.voices,
        cleanup=args.cleanup,
    ))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] in {"healthy", "idle"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
