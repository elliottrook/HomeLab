"""Owner-only vectorization and content-free dense-encoder v2 evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Callable

import nlu_encoder_candidate_v2 as candidate
import nlu_encoder_crossset_v2 as crossset


SCHEMA = "aster-nlu-encoder-crossset-result.v2"
BATCH = 24


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize(vector: list[float]) -> list[float]:
    if not vector or any(type(value) not in {int, float} or not math.isfinite(value)
                         for value in vector):
        raise ValueError("embedding vector differs")
    norm = math.sqrt(sum(float(value) ** 2 for value in vector))
    if norm <= 0:
        raise ValueError("embedding vector has no norm")
    return [float(value) / norm for value in vector]


def endpoint_embed(endpoint: str, texts: list[str]) -> list[list[float]]:
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"input": texts, "model": "bge-small-en-v1.5"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.load(response)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or len(data) != len(texts):
        raise ValueError("embedding response count differs")
    ordered = sorted(data, key=lambda item: item.get("index", -1))
    return [_normalize(item.get("embedding")) for item in ordered]


def load_set(directory: Path, embed: Callable[[list[str]], list[list[float]]]):
    cases_path = directory / "cases.json"
    labels_path = directory / "labels.json"
    cases_doc = json.loads(cases_path.read_bytes())
    labels_doc = json.loads(labels_path.read_bytes())
    cases = cases_doc.get("cases") if isinstance(cases_doc, dict) else None
    labels = labels_doc.get("labels") if isinstance(labels_doc, dict) else None
    if not isinstance(cases, list) or not isinstance(labels, list) or len(cases) != 60:
        raise ValueError("encoder set requires sixty cases and labels")
    by_id = {}
    for row in labels:
        if not isinstance(row, dict) or set(row) != {"id", "label"}:
            raise ValueError("label row differs")
        if row["id"] in by_id:
            raise ValueError("duplicate label identifier")
        candidate._label_key(row["label"])
        by_id[row["id"]] = row["label"]
    texts = []
    ordered = []
    seen = set()
    for row in cases:
        if not isinstance(row, dict) or set(row) != {"id", "family", "text"}:
            raise ValueError("case row differs")
        if row["id"] in seen or row["id"] not in by_id:
            raise ValueError("case identifier differs")
        if not isinstance(row["text"], str) or not row["text"]:
            raise ValueError("case text differs")
        if by_id[row["id"]]["request_family"] != row["family"]:
            raise ValueError("case family differs")
        seen.add(row["id"])
        texts.append(row["text"])
        ordered.append((row["id"], row["family"], by_id[row["id"]]))
    if seen != set(by_id):
        raise ValueError("label identifiers differ")
    vectors = []
    for start in range(0, len(texts), BATCH):
        vectors.extend(embed(texts[start:start + BATCH]))
    if len(vectors) != len(ordered):
        raise ValueError("embedding count differs")
    rows = [
        {"id": case_id, "family": family, "vector": vector, "expected": expected}
        for (case_id, family, expected), vector in zip(ordered, vectors)
    ]
    return rows, {
        "cases": len(rows),
        "family_counts": dict(sorted(Counter(row["family"] for row in rows).items())),
        "source_sha256": _sha(cases_path),
        "labels_sha256": _sha(labels_path),
    }


def run(root: Path, endpoint: str) -> dict:
    started = time.monotonic()
    sets = {}
    receipts = {}
    for name in ("v1", "v2", "v3", "v4", "v5", "v6"):
        sets[name], receipts[name] = load_set(
            root / name, lambda texts: endpoint_embed(endpoint, texts)
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
