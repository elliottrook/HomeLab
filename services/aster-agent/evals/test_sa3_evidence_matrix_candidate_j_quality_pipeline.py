import json
import unittest

from sa3_evidence_matrix_candidate_j_quality_blind_review import RUBRIC
from sa3_evidence_matrix_candidate_j_quality_decision import decide
from sa3_evidence_matrix_candidate_j_quality_freeze import build, canonical
from sa3_evidence_matrix_candidate_j_quality_reconciliation import reconcile
from sa3_evidence_matrix_candidate_j_quality_review_handoff import build_handoff
from sa3_evidence_matrix_candidate_j_quality_runtime import run_quality
from sa3_evidence_matrix_candidate_j_release_candidate import build as release


BOOKING = "aster-stream-a-sa3-candidate-j-quality-pipeline-test"


class CandidateJQualityPipelineTests(unittest.TestCase):
    def test_complete_pipeline_reaches_owner_review_without_effect(self):
        packet, keys = build(); tick = [0.0]
        keyed = {row["id"]: row for row in keys["case_answer_keys"]}
        prompt_ids = {case["prompt"]: case["id"] for case in packet["cases"]}
        def monotonic(): tick[0] += 0.01; return tick[0]
        def transport(payload):
            request = json.loads(payload["messages"][1]["content"])
            selected = keyed[prompt_ids[request["prompt"]]]["expected_hypothesis_ids"]
            return {"choices": [{"message": {"role": "assistant", "content":
                json.dumps({"hypothesis_ids": selected})}, "finish_reason": "stop"}]}
        result = run_quality(packet, transport, model="hidden-model",
                             monotonic=monotonic)
        terminal = {
            "schema": "aster-lab-hours-booked-result.v1", "state": "complete",
            "booking_id": BOOKING, "started_epoch": 100, "finished_epoch": 200,
            "request_count": 20,
            "workload": "sa3-evidence-matrix-candidate-j-quality-v1",
            "production_restored": True,
        }
        reconciled = reconcile(BOOKING, canonical(terminal), packet, keys,
                               canonical(result))
        reconciled.update(booking_sha256="1" * 64,
                          owner_receipt_sha256="2" * 64)
        handoff = build_handoff(packet, result)
        responses = []
        for number in range(3):
            response = json.loads(json.dumps(handoff["review_template"]))
            response["reviewer"] = f"independent-{number}"
            for row in response["reviews"]:
                row["judgments"] = dict.fromkeys(RUBRIC, True)
            responses.append(response)
        decision = decide(packet, keys, result, responses)
        candidate = release(decision, reconciled)
        self.assertTrue(reconciled["deterministic_gate_met"])
        self.assertTrue(decision["quality_gate_met"])
        self.assertEqual("ready-for-owner-D4-release-review",
                         candidate["candidate_status"])
        self.assertFalse(candidate["deployment_authorized"])
        self.assertEqual(BOOKING, candidate["booking_id"])
        self.assertEqual(reconciled["result_file_sha256"],
                         candidate["result_file_sha256"])
        self.assertEqual("none", candidate["authority"])
        self.assertEqual("off", candidate["automatic_routing"])
        self.assertNotIn("hidden-model", json.dumps(candidate))


if __name__ == "__main__":
    unittest.main()
