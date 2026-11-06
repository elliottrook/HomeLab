#!/usr/bin/env python3
"""Compare the data lexicon with the exact pinned canonical cleanup module."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import stat

from pronunciation_lexicon import apply, digest, load_corpus, load_lexicon


HERE = Path(__file__).resolve().parent


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    args = parser.parse_args(argv)
    info = args.canonical.lstat()
    if (not stat.S_ISREG(info.st_mode) or args.canonical.is_symlink()
            or info.st_nlink != 1 or info.st_size > 256 * 1024):
        raise SystemExit("CANONICAL_CUSTODY")
    lexicon, rules = load_lexicon(HERE / "pronunciation-lexicon-v1.json")
    if digest(args.canonical) != lexicon["canonical_cleanup_sha256"]:
        raise SystemExit("CANONICAL_DRIFT")
    spec = importlib.util.spec_from_file_location("aster_canonical_cleanup", args.canonical)
    if spec is None or spec.loader is None:
        raise SystemExit("CANONICAL_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = load_corpus(HERE / "retained-corpus-v1.json", lexicon_id=lexicon["id"])
    for case in cases:
        candidate = apply(case["input"], rules)
        canonical = module.speech_text(case["input"])
        if candidate != canonical or canonical != case["expected"]:
            raise SystemExit("CANONICAL_MISMATCH:" + case["id"])
    print(json.dumps({"canonical_sha256": lexicon["canonical_cleanup_sha256"],
                      "cases": len(cases), "lexicon_id": lexicon["id"],
                      "outcome": "byte-identical"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
