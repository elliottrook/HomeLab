"""Create Candidate-J's model-blind review handoff from one eligible result."""

from __future__ import annotations

import json
from pathlib import Path

from sa3_evidence_matrix_candidate_j_quality_blind_review import (
    build_review_packet, review_packet_sha256, template,
)


def build_handoff(packet: dict, result: dict) -> dict[str, object]:
    review_packet = build_review_packet(packet, result)
    review_template = template(review_packet)
    return {
        "schema": "aster-sa3-evidence-matrix-candidate-j-review-handoff.v1",
        "candidate_alias": "candidate-j",
        "model_identity_disclosed": False,
        "review_packet_sha256": review_packet_sha256(review_packet),
        "review_packet": review_packet,
        "review_template": review_template,
        "required_distinct_reviewers": 3,
        "authority": "none",
        "automatic_routing": "off",
        "promotion": "not-authorized",
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    value = build_handoff(
        json.loads(args.packet.read_text(encoding="utf-8")),
        json.loads(args.result.read_text(encoding="utf-8")),
    )
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
