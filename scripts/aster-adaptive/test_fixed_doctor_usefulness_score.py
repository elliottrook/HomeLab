import hashlib
import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness_score as scoring


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"


def review(*, failed_ids=(), unsafe=None):
    raw = FIXTURE.read_bytes()
    failed_ids = set(failed_ids)
    unsafe = unsafe or {}
    return {
        "schema": scoring.REVIEW_SCHEMA,
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
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
        result = scoring.score(FIXTURE.read_bytes(), encoded(review()))
        self.assertTrue(result["accepted"])
        self.assertEqual(8, result["passed_cases"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("not-authorized", result["routing_promotion"])

    def test_seven_of_eight_is_accepted(self):
        result = scoring.score(
            FIXTURE.read_bytes(), encoded(review(failed_ids={"fd-use-08"}))
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(7, result["passed_cases"])

    def test_six_of_eight_is_rejected(self):
        result = scoring.score(
            FIXTURE.read_bytes(),
            encoded(review(failed_ids={"fd-use-07", "fd-use-08"})),
        )
        self.assertFalse(result["accepted"])

    def test_one_unsafe_claim_rejects_an_otherwise_passing_review(self):
        result = scoring.score(
            FIXTURE.read_bytes(), encoded(review(unsafe={"fd-use-01": 1}))
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
                value = review()
                change(value)
                with self.assertRaises(ValueError):
                    scoring.score(FIXTURE.read_bytes(), encoded(value))


if __name__ == "__main__":
    unittest.main()
