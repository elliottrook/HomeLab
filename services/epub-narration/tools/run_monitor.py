#!/usr/bin/env python3
"""Run one content-silent catalogue reconciliation pass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from epub_narration import COMPILER_CONTRACT
from epub_narration.monitor import reconcile_catalogue


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    args = parser.parse_args()
    result = reconcile_catalogue(
        database=args.database,
        library_root=args.library_root,
        state_root=args.state_root,
        compiler_contract=COMPILER_CONTRACT,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
