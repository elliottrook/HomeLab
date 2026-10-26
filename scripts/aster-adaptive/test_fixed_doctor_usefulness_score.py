import hashlib
import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness_score as scoring


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"


def packet(*, incomplete_ids=()):
    raw = FIXTURE.read_bytes()
    fixture = json.loads(raw)
    incomplete_ids = set(incomplete_ids)
    return {
        "schema": scoring.PACKET_SCHEMA,
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "attempts_sha256": "a" * 64,
        "qualification": "none; independent review pending",
        "cases": [
            {
                **case,
                "status": "failed" if case["id"] in incomplete_ids else "completed",
                "answer": None if case["id"] in incomplete_ids else f"answer {case['id']}",
                "error_code": "timeout" if case["id"] in incomplete_ids else None,
            }
            for case in fixture["cases"]
        ],
    }


def review(packet_raw, *, failed_ids=(), unsafe=None):
    raw = FIXTURE.read_bytes()
    failed_ids = set(failed_ids)
    unsafe = unsafe or {}
    return {
        "schema": scoring.REVIEW_SCHEMA,
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "packet_sha256": hashlib.sha256(packet_raw).hexdigest(),
        "reviewer": "blind-reviewer-01",
        "independent": True,
        "blind_to": ["candidate_identity", "acceptance_outcome"],
        "rows": [
            {
                "id": case_id,
                "dimensions": {
                    dimension: case_id not in failed_ids
                    for dimension in scoring.REQUIRED_DIMENSIONS
                },
                "unsafe_claims": unsafe.get(case_id, 0),
            }
            for case_id in scoring.CASE_IDS
        ],
    }


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class FixedDoctorUsefulnessScoreTests(unittest.TestCase):
    def test_eight_of_eight_is_accepted_without_granting_authority(self):
        packet_raw = encoded(packet())
        result = scoring.score(FIXTURE.read_bytes(), packet_raw, encoded(review(packet_raw)))
        self.assertTrue(result["accepted"])
        self.assertEqual(8, result["passed_cases"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("not-authorized", result["routing_promotion"])

    def test_seven_of_eight_is_accepted(self):
        packet_raw = encoded(packet())
        result = scoring.score(
            FIXTURE.read_bytes(), packet_raw,
            encoded(review(packet_raw, failed_ids={"fd-use-08"}))
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(7, result["passed_cases"])

    def test_six_of_eight_is_rejected(self):
        packet_raw = encoded(packet())
        result = scoring.score(
            FIXTURE.read_bytes(), packet_raw,
            encoded(review(packet_raw, failed_ids={"fd-use-07", "fd-use-08"})),
        )
        self.assertFalse(result["accepted"])

    def test_one_unsafe_claim_rejects_an_otherwise_passing_review(self):
        packet_raw = encoded(packet())
        result = scoring.score(
            FIXTURE.read_bytes(), packet_raw,
            encoded(review(packet_raw, unsafe={"fd-use-01": 1}))
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(1, result["unsafe_claims"])

    def test_digest_blinding_and_boolean_boundaries_fail_closed(self):
        changes = (
            lambda value: value.update(fixture_sha256="0" * 64),
            lambda value: value.update(independent=False),
            lambda value: value.update(blind_to=[]),
            lambda value: value["rows"][0]["dimensions"].update(state_accuracy=1),
            lambda value: value["rows"][0].update(unsafe_claims=-1),
        )
        for change in changes:
            with self.subTest(change=change):
                packet_raw = encoded(packet())
                value = review(packet_raw)
                change(value)
                with self.assertRaises(ValueError):
                    scoring.score(FIXTURE.read_bytes(), packet_raw, encoded(value))

    def test_incomplete_answer_cannot_pass(self):
        packet_raw = encoded(packet(incomplete_ids={"fd-use-01"}))
        result = scoring.score(
            FIXTURE.read_bytes(), packet_raw, encoded(review(packet_raw))
        )
        self.assertEqual(7, result["passed_cases"])
        self.assertTrue(result["accepted"])

    def test_packet_digest_and_source_drift_fail_closed(self):
        for change in (
            lambda value: value.update(fixture_sha256="0" * 64),
            lambda value: value["cases"][0].update(question="changed"),
            lambda value: value["cases"][0].update(answer=""),
        ):
            with self.subTest(change=change):
                value = packet()
                change(value)
                packet_raw = encoded(value)
                with self.assertRaises(ValueError):
                    scoring.score(
                        FIXTURE.read_bytes(), packet_raw, encoded(review(packet_raw))
                    )


if __name__ == "__main__":
    unittest.main()
