#!/usr/bin/env python3
"""Create a root-private benchmark plan and print only aggregate structure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration.benchmark import create_private_plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-count", type=int, default=20)
    parser.add_argument("--sample-words", type=int, default=1500)
    args = parser.parse_args()
    summary = create_private_plan(
        args.database,
        args.library_root,
        args.output,
        sample_count=args.sample_count,
        sample_words=args.sample_words,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
