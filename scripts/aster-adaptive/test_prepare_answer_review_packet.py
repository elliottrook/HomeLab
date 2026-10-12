import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from capture_answer_feasibility import capture
from prepare_answer_review_packet import prepare, save
from score_answer_feasibility import score


FIXTURE = Path(__file__).with_name("fixtures") / "answer-feasibility-v0.json"


def fake_attempts(fixture_raw):
    fixture = json.loads(fixture_raw)
    return json.dumps({
        "schema_version": "aster-answer-capture.v0",
        "fixture_sha256": hashlib.sha256(fixture_raw).hexdigest(),
        "candidate_profile_sha256": "a" * 64,
        "tool_mode": "disabled",
        "attempts": [{"case_id": case["id"], "status": "completed",
                      "answer": "Synthetic answer for " + case["id"],
                      "source_ids": [], "error_code": None,
                      "route_ms": None, "context_ms": None,
                      "inference_ms": None, "total_ms": 100}
                     for case in fixture["cases"]],
    }).encode()


class ReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FIXTURE.read_bytes()
        self.attempts = fake_attempts(self.fixture)
        self.captured = json.dumps(capture(self.fixture, self.attempts),
                                   sort_keys=True).encode()

    def test_packet_has_answers_and_rubric_but_no_backend_identity(self):
        packet_raw, template_raw = prepare(self.fixture, self.attempts, self.captured)
        packet, template = json.loads(packet_raw), json.loads(template_raw)
        self.assertEqual(len(packet["cases"]), 6)
        self.assertEqual(len(template["reviews"]), 6)
        self.assertIn("Synthetic answer", packet["cases"][0]["answer"])
        self.assertNotIn("candidate_profile_sha256", packet_raw.decode())
        self.assertIsNone(template["reviewer_id"])
        self.assertTrue(all(value is None for value in template["reviews"][0]["rubric_checks"]))
        with self.assertRaises(ValueError):
            score(self.fixture, self.captured, template_raw)

    def test_rejects_capture_not_bound_to_attempts(self):
        changed_capture = json.loads(self.captured)
        changed_capture["attempts"][0]["total_ms"] += 1
        changed = json.dumps(changed_capture).encode()
        with self.assertRaises(ValueError):
            prepare(self.fixture, self.attempts, changed)

    def test_private_output_and_no_overwrite(self):
        packet, template = prepare(self.fixture, self.attempts, self.captured)
        with tempfile.TemporaryDirectory() as parent:
            target = Path(parent) / "review"
            receipt = save(target, packet, template)
            self.assertEqual(receipt["case_count"], 6)
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o700)
            for name in ("review-packet.json", "review-template.json"):
                self.assertEqual(os.stat(target / name).st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                save(target, packet, template)


if __name__ == "__main__":
    unittest.main()
