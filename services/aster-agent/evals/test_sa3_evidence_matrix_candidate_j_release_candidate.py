import copy
import unittest

from sa3_evidence_matrix_candidate_j_quality_blind_review import (
    RUBRIC, build_review_packet, review_packet_sha256,
)
from sa3_evidence_matrix_candidate_j_quality_decision import decide
from sa3_evidence_matrix_candidate_j_quality_freeze import build as freeze, canonical
from sa3_evidence_matrix_candidate_j_quality_reconciliation import reconcile
from sa3_evidence_matrix_candidate_j_release_candidate import build
from test_sa3_evidence_matrix_candidate_j_quality_blind_review import complete_result


BOOKING = "aster-stream-a-sa3-candidate-j-quality-release-test"


def passing_inputs():
    packet, keys = freeze(); result = complete_result(packet, keys)
    review_packet = build_review_packet(packet, result)
    responses = [{
        "schema": "aster-sa3-evidence-matrix-candidate-j-blind-review.v1",
        "review_packet_sha256": review_packet_sha256(review_packet),
        "reviewer": f"independent-{number}", "model_blind": True,
        "reviews": [{"id": row["id"],
                     "judgments": dict.fromkeys(RUBRIC, True)}
                    for row in review_packet["cases"]],
    } for number in range(3)]
    decision = decide(packet, keys, result, responses)
    terminal = {"schema": "aster-lab-hours-booked-result.v1",
                "state": "complete", "booking_id": BOOKING,
                "started_epoch": 100, "finished_epoch": 200,
                "request_count": 20,
                "workload": "sa3-evidence-matrix-candidate-j-quality-v1",
                "production_restored": True}
    reconciliation = reconcile(BOOKING, canonical(terminal), packet, keys,
                               canonical(result))
    return decision, reconciliation


class CandidateJReleaseCandidateTests(unittest.TestCase):
    def test_passing_decision_builds_owner_review_not_deployment(self):
        value = build(*passing_inputs())
        self.assertEqual("ready-for-owner-D4-release-review",
                         value["candidate_status"])
        self.assertTrue(value["owner_decision_required"])
        self.assertFalse(value["deployment_authorized"])
        self.assertEqual("not-authorized", value["promotion"])

    def test_failed_or_broadened_decision_fails_closed(self):
        for field, changed in (("quality_gate_met", False),
                               ("promotion", "authorized"),
                               ("automatic_routing", "on"),
                               ("abstentions_passed", 5)):
            decision, reconciliation = passing_inputs()
            value = copy.deepcopy(decision); value[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                build(value, reconciliation)

    def test_missing_or_mismatched_reconciliation_fails_closed(self):
        decision, reconciliation = passing_inputs()
        with self.assertRaises(ValueError):
            build(decision, {})
        changed = copy.deepcopy(reconciliation)
        changed["result_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "reconciliation"):
            build(decision, changed)


if __name__ == "__main__":
    unittest.main()
