"""Build a bounded owner-review packet from a passing Candidate-J decision."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from sa3_evidence_matrix_candidate_j_quality_result_contract import decode_unique


DECISION_FIELDS = {
    "schema", "candidate_alias", "packet_sha256", "keys_sha256",
    "result_sha256", "review_packet_sha256", "review_response_sha256",
    "reviewer_count", "review_independence", "case_count", "passed",
    "required_passes",
    "abstentions", "abstentions_passed", "no_false_completion_failures",
    "quality_gate_met", "authority", "automatic_routing", "promotion",
    "limit",
}
RECONCILIATION_FIELDS = {
    "schema", "booking_id", "state", "terminal_sha256",
    "production_restored", "case_count", "passed", "required_passes",
    "model_request_count", "deterministic_abstentions", "abstentions_passed",
    "retry_count", "false_completion_failures", "result_file_sha256",
    "result_sha256", "deterministic_gate_met", "model_identity_disclosed",
    "authority", "automatic_routing", "quality_decision", "promotion",
    "booking_sha256", "owner_receipt_sha256",
}
HEX64 = re.compile(r"[0-9a-f]{64}")


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def build(decision: object, reconciliation: object) -> dict[str, object]:
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
            or decision["review_independence"]
            != "separate-execution-not-authenticated-custody"
            or not isinstance(decision["review_response_sha256"], list)
            or len(decision["review_response_sha256"]) != 3
            or len(set(decision["review_response_sha256"])) != 3
            or any(not isinstance(value, str) or not HEX64.fullmatch(value)
                   for value in decision["review_response_sha256"])
            or any(not isinstance(decision[field], str)
                   or not HEX64.fullmatch(decision[field])
                   for field in ("packet_sha256", "keys_sha256",
                                 "result_sha256", "review_packet_sha256"))
            or decision["authority"] != "none"
            or decision["automatic_routing"] != "off"
            or decision["promotion"] != "not-authorized"):
        raise ValueError("Candidate-J decision is not release-candidate eligible")
    if (not isinstance(reconciliation, dict)
            or set(reconciliation) != RECONCILIATION_FIELDS
            or reconciliation["schema"]
            != "aster-sa3-evidence-matrix-quality-reconciliation.v1"
            or not isinstance(reconciliation["booking_id"], str)
            or not reconciliation["booking_id"]
            or reconciliation["state"] != "complete"
            or reconciliation["production_restored"] is not True
            or reconciliation["case_count"] != 20
            or reconciliation["model_request_count"] != 14
            or reconciliation["deterministic_abstentions"] != 6
            or reconciliation["retry_count"] != 0
            or reconciliation["deterministic_gate_met"] is not True
            or reconciliation["model_identity_disclosed"] is not False
            or reconciliation["result_sha256"] != decision["result_sha256"]
            or reconciliation["authority"] != "none"
            or reconciliation["automatic_routing"] != "off"
            or reconciliation["promotion"] != "not-authorized"
            or any(not isinstance(reconciliation[field], str)
                   or not HEX64.fullmatch(reconciliation[field])
                   for field in ("booking_sha256", "owner_receipt_sha256",
                                 "terminal_sha256", "result_file_sha256",
                                 "result_sha256"))):
        raise ValueError("Candidate-J reconciliation is not release-candidate eligible")
    return {
        "schema": "aster-sa3-evidence-matrix-candidate-j-release-candidate.v1",
        "candidate_alias": "candidate-j",
        "decision_sha256": hashlib.sha256(canonical(decision)).hexdigest(),
        "reconciliation_sha256":
            hashlib.sha256(canonical(reconciliation)).hexdigest(),
        "booking_id": reconciliation["booking_id"],
        "booking_sha256": reconciliation["booking_sha256"],
        "owner_receipt_sha256": reconciliation["owner_receipt_sha256"],
        "terminal_sha256": reconciliation["terminal_sha256"],
        "packet_sha256": decision["packet_sha256"],
        "result_file_sha256": reconciliation["result_file_sha256"],
        "result_sha256": decision["result_sha256"],
        "review_packet_sha256": decision["review_packet_sha256"],
        "review_response_sha256": decision["review_response_sha256"],
        "reviewer_count": 3,
        "review_independence": decision["review_independence"],
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
    parser.add_argument("reconciliation", type=Path)
    args = parser.parse_args(argv)
    value = build(decode_unique(args.decision.read_bytes()),
                  decode_unique(args.reconciliation.read_bytes()))
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
