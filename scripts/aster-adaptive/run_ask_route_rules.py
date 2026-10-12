"""Run the existing fixture-authored lexical rules as a tool-free comparator.

Development regression only. This is not an independent quality estimate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from routing_smoke import rules


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.fixture.read_bytes()
    fixture = json.loads(raw)
    if fixture.get("schema_version") != "routing-families.v1":
        raise ValueError("unexpected fixture schema")
    records = []
    for case in fixture["families"]:
        start = time.perf_counter()
        decision = rules(case["text"])
        elapsed = time.perf_counter() - start
        if decision.get("authorization") != "not-granted" or decision.get("confidence") is not None:
            raise ValueError("rule output crossed the no-authority comparator boundary")
        records.append({"id": case["id"], "valid": True,
                        "status": decision["status"],
                        "capabilities": decision["labels"],
                        "latency_seconds": elapsed})
    result = {"schema": "aster-ask-route-run.v1",
              "model": "existing-lexical-rules",
              "fixture_sha256": hashlib.sha256(raw).hexdigest(),
              "attempted": len(records), "valid": len(records),
              "records": records}
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
