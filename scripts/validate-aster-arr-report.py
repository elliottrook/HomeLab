#!/usr/bin/env python3
"""Validate a candidate sanitized ARR report without contacting any service."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/aster-agent"))

from arr_report import get_arr_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="candidate JSON report")
    parser.add_argument("--freshness-seconds", type=int, default=900)
    args = parser.parse_args()
    if args.freshness_seconds <= 0:
        parser.error("--freshness-seconds must be positive")
    result = get_arr_report(args.report, freshness_seconds=args.freshness_seconds)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") != "unavailable" else 1


if __name__ == "__main__":
    raise SystemExit(main())
