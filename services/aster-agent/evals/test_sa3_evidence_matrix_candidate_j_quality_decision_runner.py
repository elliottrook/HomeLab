import json
import tempfile
import unittest
from pathlib import Path

from sa3_evidence_matrix_candidate_j_quality_blind_review import (
    RUBRIC, build_review_packet, review_packet_sha256,
)
from sa3_evidence_matrix_candidate_j_quality_decision_runner import run
from sa3_evidence_matrix_candidate_j_quality_freeze import build, canonical
from test_sa3_evidence_matrix_candidate_j_quality_blind_review import complete_result


class CandidateJQualityDecisionRunnerTests(unittest.TestCase):
    def test_exact_three_file_decision_is_quality_only(self):
        packet, keys = build(); result = complete_result(packet, keys)
        review_packet = build_review_packet(packet, result)
        responses = [{
            "schema": "aster-sa3-evidence-matrix-candidate-j-blind-review.v1",
            "review_packet_sha256": review_packet_sha256(review_packet),
            "reviewer": f"independent-{number}", "model_blind": True,
            "reviews": [{"id": row["id"],
                         "judgments": dict.fromkeys(RUBRIC, True)}
                        for row in review_packet["cases"]],
        } for number in range(3)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for name, value in (("packet", packet), ("keys", keys),
                                ("result", result)):
                path = root / f"{name}.json"; path.write_bytes(canonical(value))
                paths.append(path)
            reviews = []
            for number, value in enumerate(responses):
                path = root / f"review-{number}.json"; path.write_bytes(canonical(value))
                reviews.append(path)
            decision = run(*paths, reviews)
        self.assertTrue(decision["quality_gate_met"])
        self.assertEqual("not-authorized", decision["promotion"])
        self.assertNotIn(result["model"], json.dumps(decision))

    def test_review_count_fails_closed_before_read(self):
        with self.assertRaisesRegex(ValueError, "exactly three"):
            run(Path("missing"), Path("missing"), Path("missing"), [])


if __name__ == "__main__":
    unittest.main()
