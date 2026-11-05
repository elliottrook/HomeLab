import copy
import unittest

from sa3_evidence_matrix_candidate_j_quality_blind_review import (
    RUBRIC, build_review_packet, review_packet_sha256,
)
from sa3_evidence_matrix_candidate_j_quality_decision import decide
from sa3_evidence_matrix_candidate_j_quality_freeze import build as freeze
from sa3_evidence_matrix_candidate_j_release_candidate import build
from test_sa3_evidence_matrix_candidate_j_quality_blind_review import complete_result


def passing_decision():
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
    return decide(packet, keys, result, responses)


class CandidateJReleaseCandidateTests(unittest.TestCase):
    def test_passing_decision_builds_owner_review_not_deployment(self):
        value = build(passing_decision())
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
            value = copy.deepcopy(passing_decision()); value[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                build(value)


if __name__ == "__main__":
    unittest.main()
