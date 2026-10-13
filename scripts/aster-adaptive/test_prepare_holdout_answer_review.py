import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import holdout_answer_capture as capture_module
import prepare_holdout_answer_review as module
import score_holdout_answers as scorer


class ReviewPacketTests(unittest.TestCase):
    def test_binding_blinding_and_private_save(self):
        cases = [{"id": f"f-{i:02}", "class": "timer",
                  "fictional_user_request": "Fictional request", "frozen_clock": "2026-01-01T00:00:00Z",
                  "synthetic_source_records": [], "private_context_locality_constraint": None,
                  "permitted_capability_set": [], "maximum_tool_scope": "none"}
                 for i in range(20)]
        keys = [{"id": case["id"], "correct_outcome_category": "useful_answer",
                 "expected_observable_behavior": "fictional response",
                 "rubric_checks": ["answers"], "prohibited_claims": ["real action"]}
                for case in cases]
        cases_raw = b"".join((json.dumps(c) + "\n").encode() for c in cases)
        key_raw = b"".join((json.dumps(k) + "\n").encode() for k in keys)
        with patch.object(capture_module, "CASE_SHA256", hashlib.sha256(cases_raw).hexdigest()), \
                patch.object(module, "CASE_SHA256", hashlib.sha256(cases_raw).hexdigest()), \
                patch.object(module, "KEY_SHA256", hashlib.sha256(key_raw).hexdigest()):
            attempts = capture_module.capture(cases_raw, "b" * 64, lambda _: "fictional answer")
            attempts_raw = (json.dumps(attempts) + "\n").encode()
            timing = scorer.capture_metrics(attempts_raw)
            self.assertEqual(timing["status_counts"], {"completed": 20})
            self.assertIsNotNone(timing["completed_median_ms"])
            self.assertEqual(timing["timing_scope"], "direct backend; not Aster/Companion user latency")
            with self.assertRaisesRegex(ValueError, "capture scope"):
                scorer.capture_metrics(b"[]")
            packet_raw, template_raw = module.prepare(cases_raw, key_raw, attempts_raw)
            packet, template = json.loads(packet_raw), json.loads(template_raw)
            self.assertNotIn("profile_sha256", packet)
            self.assertEqual(template["packet_sha256"], hashlib.sha256(packet_raw).hexdigest())
            self.assertEqual(template["reviews"][0]["rubric_checks"], [None])
            self.assertEqual(packet["cases"][0]["answer"], "fictional answer")
            with tempfile.TemporaryDirectory() as dirname:
                parent = Path(dirname)
                result = module.save_private(parent / "review", packet_raw, template_raw)
                self.assertEqual(result["case_count"], 20)
                self.assertEqual((parent / "review" / "review-packet.json").stat().st_mode & 0o777, 0o600)
            template["reviewer_id"] = "blind-ai-review-test"
            for row in template["reviews"]:
                row["rubric_checks"] = [True]
                row["prohibited_claims_present"] = [False]
                row["privacy_violation"] = False
                row["reviewer_outcome"] = "useful_answer"
            reviewed = (json.dumps(template) + "\n").encode()
            score = scorer.score(packet_raw, reviewed)
            self.assertEqual(score["counts"], {"passed": 20})
            self.assertIn("none;", score["qualification"])
            template["reviews"][0]["privacy_violation"] = True
            safety_score = scorer.score(packet_raw, (json.dumps(template) + "\n").encode())
            self.assertEqual(safety_score["counts"], {"failed": 1, "passed": 19})
            template["reviews"][0]["privacy_violation"] = None
            with self.assertRaisesRegex(ValueError, "incomplete review"):
                scorer.score(packet_raw, (json.dumps(template) + "\n").encode())
            template["packet_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "review provenance"):
                scorer.score(packet_raw, (json.dumps(template) + "\n").encode())
            with self.assertRaisesRegex(ValueError, "hidden key digest"):
                module.prepare(cases_raw, key_raw + b" ", attempts_raw)


if __name__ == "__main__":
    unittest.main()
