"""Owner-only vectorization and content-free dense-head evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import nlu_encoder_head_crossset_v1 as crossset
import nlu_encoder_runtime_v2 as vectors


SCHEMA = "aster-nlu-encoder-head-crossset-result.v1"


def run(root: Path, endpoint: str) -> dict:
    started = time.monotonic()
    sets = {}
    receipts = {}
    for name in ("v1", "v2", "v3", "v4", "v5", "v6"):
        sets[name], receipts[name] = vectors.load_set(
            root / name, lambda texts: vectors.endpoint_embed(endpoint, texts)
        )
    result = crossset.evaluate_nested(sets)
    return {
        "schema": SCHEMA,
        "set_receipts": receipts,
        "folds": result["folds"],
        "nested_pass": result["nested_pass"],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "authority": result["authority"],
        "automatic_routing": result["automatic_routing"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sets-root", required=True, type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.sets_root, args.endpoint)
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    args.output.write_bytes(encoded)
    print(json.dumps({
        "folds": [{"outer": fold["outer"], "status": fold["status"]}
                  for fold in result["folds"]],
        "nested_pass": result["nested_pass"],
        "output_sha256": hashlib.sha256(encoded).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
