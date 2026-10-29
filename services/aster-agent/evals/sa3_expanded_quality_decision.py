"""Deterministic no-authority decision for a completed expanded-quality run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sa3_expanded_quality_blind_review import (
    build_review_packet, review_packet_sha256, validate_review,
)
from sa3_expanded_quality_packet import _canonical, _load, grade


def evaluate(packet: dict, keys: dict, result: dict, review_response: dict, *,
             candidate_alias: str) -> dict[str, object]:
    blind_packet = build_review_packet(packet, result, candidate_alias=candidate_alias)
    reviews = validate_review(blind_packet, review_response)
    report = grade(packet, keys, result["predictions"], reviews)
    return {
        "schema": "aster-sa3-expanded-quality-decision.v1",
        "candidate_alias": candidate_alias,
        "packet_id": report["packet_id"],
        "packet_sha256": report["packet_sha256"],
        "keys_sha256": report["keys_sha256"],
        "result_sha256": hashlib.sha256(_canonical(result)).hexdigest(),
        "review_packet_sha256": review_packet_sha256(blind_packet),
        "review_response_sha256": hashlib.sha256(_canonical(review_response)).hexdigest(),
        "cases": report["cases"],
        "passed": report["passed"],
        "quality_gate_met": report["quality_gate_met"],
        "limit": report["limit"],
        "routing_authorized": False,
        "repair_authorized": False,
        "model_promotion_authorized": False,
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--candidate-alias", required=True)
    args = parser.parse_args(argv)
    decision = evaluate(
        _load(args.packet), _load(args.keys), _load(args.result),
        _load(args.review), candidate_alias=args.candidate_alias,
    )
    print(json.dumps(decision, sort_keys=True))
    return 0 if decision["quality_gate_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
