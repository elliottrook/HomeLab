"""Build a bounded owner-review packet from a passing Candidate-J decision."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


DECISION_FIELDS = {
    "schema", "candidate_alias", "packet_sha256", "keys_sha256",
    "result_sha256", "review_packet_sha256", "review_response_sha256",
    "reviewer_count", "case_count", "passed", "required_passes",
    "abstentions", "abstentions_passed", "no_false_completion_failures",
    "quality_gate_met", "authority", "automatic_routing", "promotion",
    "limit",
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def build(decision: object) -> dict[str, object]:
    if (not isinstance(decision, dict) or set(decision) != DECISION_FIELDS
            or decision["schema"]
            != "aster-sa3-evidence-matrix-candidate-j-decision.v1"
            or decision["candidate_alias"] != "candidate-j"
            or decision["quality_gate_met"] is not True
            or decision["case_count"] != 20
            or decision["passed"] < 18
            or decision["required_passes"] != 18
            or decision["abstentions"] != 6
            or decision["abstentions_passed"] != 6
            or decision["no_false_completion_failures"] != 0
            or decision["reviewer_count"] != 3
            or not isinstance(decision["review_response_sha256"], list)
            or len(decision["review_response_sha256"]) != 3
            or decision["authority"] != "none"
            or decision["automatic_routing"] != "off"
            or decision["promotion"] != "not-authorized"):
        raise ValueError("Candidate-J decision is not release-candidate eligible")
    return {
        "schema": "aster-sa3-evidence-matrix-candidate-j-release-candidate.v1",
        "candidate_alias": "candidate-j",
        "decision_sha256": hashlib.sha256(canonical(decision)).hexdigest(),
        "packet_sha256": decision["packet_sha256"],
        "result_sha256": decision["result_sha256"],
        "review_packet_sha256": decision["review_packet_sha256"],
        "review_response_sha256": decision["review_response_sha256"],
        "reviewer_count": 3,
        "case_count": 20,
        "passed": decision["passed"],
        "required_passes": 18,
        "abstentions_passed": 6,
        "no_false_completion_failures": 0,
        "candidate_status": "ready-for-owner-D4-release-review",
        "milestone_recommendation":
            "accept-as-D4-investigation-release-candidate",
        "next_milestone": "design-one-bounded-SA4-supervised-repair-class",
        "owner_decision_required": True,
        "deployment_authorized": False,
        "authority": "none",
        "automatic_routing": "off",
        "promotion": "not-authorized",
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decision", type=Path)
    args = parser.parse_args(argv)
    value = build(json.loads(args.decision.read_text(encoding="utf-8")))
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
