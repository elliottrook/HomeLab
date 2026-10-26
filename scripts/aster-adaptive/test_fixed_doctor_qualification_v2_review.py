import hashlib
import json
import unittest

import fixed_doctor_deterministic_answer as formatter
import fixed_doctor_qualification_v2 as qualification
import fixed_doctor_qualification_v2_score as scoring
import prepare_fixed_doctor_qualification_v2_review as prepare
from test_fixed_doctor_qualification_v2 import packet

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2] / "services" / "aster-agent"))
from fixed_doctor_response import render_observation


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def artifacts():
    source_raw = encode(packet())
    attempts = {"schema": prepare.ATTEMPTS_SCHEMA,
                "source_sha256": hashlib.sha256(source_raw).hexdigest(),
                "method": "deterministic-fixed-doctor-v1", "tool_mode": "disabled",
                "authority": "not-granted",
                "rows": [{"id": case["id"], "status": "completed",
                          "answer": formatter.answer(case), "error_code": None}
                         for case in packet()["cases"]]}
    packet_raw, blank_raw = prepare.prepare(source_raw, encode(attempts))
    return source_raw, packet_raw, json.loads(blank_raw)


class QualificationReviewTests(unittest.TestCase):
    def test_production_renderer_is_equivalent_on_qualification_cases(self):
        for case in packet()["cases"]:
            self.assertEqual(formatter.answer(case), render_observation(case["observation"]))

    def test_twelve_of_twelve_accepts_without_authority(self):
        source_raw, packet_raw, review = artifacts()
        review["reviewer"] = "fixed-doctor-blind-reviewer-04"
        for row in review["rows"]:
            row["dimensions"] = {dimension: True for dimension in qualification.REQUIRED_DIMENSIONS}
            row["unsafe_claims"] = 0
        result = scoring.score(source_raw, packet_raw, encode(review))
        self.assertTrue(result["accepted"])
        self.assertEqual(12, result["passed_cases"])
        self.assertEqual("not-granted", result["authority"])

    def test_one_failed_dimension_rejects(self):
        source_raw, packet_raw, review = artifacts()
        review["reviewer"] = "fixed-doctor-blind-reviewer-04"
        for row in review["rows"]:
            row["dimensions"] = {dimension: True for dimension in qualification.REQUIRED_DIMENSIONS}
            row["unsafe_claims"] = 0
        review["rows"][0]["dimensions"]["freshness"] = False
        result = scoring.score(source_raw, packet_raw, encode(review))
        self.assertFalse(result["accepted"])
        self.assertEqual(11, result["passed_cases"])

    def test_digest_and_blinding_drift_fail_closed(self):
        source_raw, packet_raw, review = artifacts()
        review["reviewer"] = "fixed-doctor-blind-reviewer-04"
        review["packet_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            scoring.score(source_raw, packet_raw, encode(review))


if __name__ == "__main__":
    unittest.main()
