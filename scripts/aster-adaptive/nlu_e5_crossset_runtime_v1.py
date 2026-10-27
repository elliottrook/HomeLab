"""Owner-only E5 query/passage vectorization for the six-set nested gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

import nlu_e5_public_gate_v1 as endpoint
import nlu_encoder_candidate_v2 as candidate
import nlu_e5_crossset_v1 as crossset


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_set(directory, embed):
    cases_path, labels_path = directory / "cases.json", directory / "labels.json"
    cases_doc, labels_doc = json.loads(cases_path.read_bytes()), json.loads(labels_path.read_bytes())
    cases, labels = cases_doc.get("cases"), labels_doc.get("labels")
    if not isinstance(cases, list) or not isinstance(labels, list) or len(cases) != 60:
        raise ValueError("E5 set requires sixty cases and labels")
    by_id = {}
    for row in labels:
        if not isinstance(row, dict) or set(row) != {"id", "label"} or row["id"] in by_id:
            raise ValueError("label row differs")
        candidate._label_key(row["label"])
        by_id[row["id"]] = row["label"]
    texts, ordered, seen = [], [], set()
    for row in cases:
        if (not isinstance(row, dict) or set(row) != {"id", "family", "text"}
                or row["id"] in seen or row["id"] not in by_id):
            raise ValueError("case row differs")
        if not isinstance(row["text"], str) or not row["text"]:
            raise ValueError("case text differs")
        expected = by_id[row["id"]]
        if expected["request_family"] != row["family"]:
            raise ValueError("case family differs")
        seen.add(row["id"]); texts.append(row["text"])
        ordered.append((row["id"], row["family"], expected))
    if seen != set(by_id):
        raise ValueError("label identifiers differ")
    passages, queries = [], []
    for start in range(0, len(texts), 24):
        chunk = texts[start:start + 24]
        passages.extend(embed(["passage: " + text for text in chunk]))
        queries.extend(embed(["query: " + text for text in chunk]))
    return [
        {"id": case_id, "family": family, "passage_vector": passage,
         "query_vector": query, "expected": expected}
        for (case_id, family, expected), passage, query in zip(ordered, passages, queries)
    ], {"cases": len(ordered),
        "family_counts": dict(sorted(Counter(family for _, family, _ in ordered).items())),
        "source_sha256": _sha(cases_path), "labels_sha256": _sha(labels_path)}


def run(root, endpoint_url):
    started = time.monotonic(); sets, receipts = {}, {}
    embed = lambda texts: endpoint.endpoint_embed(endpoint_url, texts)
    for name in ("v1", "v2", "v3", "v4", "v5", "v6"):
        sets[name], receipts[name] = load_set(root / name, embed)
    result = crossset.evaluate_nested(sets)
    return {"schema": "aster-nlu-e5-crossset-result.v1", "set_receipts": receipts,
            "folds": result["folds"], "nested_pass": result["nested_pass"],
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "authority": result["authority"],
            "automatic_routing": result["automatic_routing"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sets-root", required=True, type=Path)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(); result = run(args.sets_root, args.endpoint)
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    args.output.write_bytes(encoded)
    print(json.dumps({"folds": [{"outer": x["outer"], "status": x["status"]} for x in result["folds"]],
                      "nested_pass": result["nested_pass"],
                      "output_sha256": hashlib.sha256(encoded).hexdigest()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
