import copy
import unittest

from validate_sa3_holdout_release import canonical_digest, validate_release


def digest(character):
    return character * 64


def sealed_release():
    value = {
        "schema_version": 1,
        "status": "sealed",
        "release_id": "sa3-holdout-v1",
        "target_cases": 20,
        "roles": {
            "custodian_session": "custodian-2026-09-28",
            "review_session": "review-2026-09-28",
            "evaluation_session": "evaluation-2026-09-28",
            "scoring_session": "scoring-2026-09-28",
        },
        "cases": [
            {
                "id": f"SA3-HO-{index:03d}",
                "family": "sanitized_family",
                "case_hash": digest("a"),
                "label_hash": digest("b"),
                "review_receipt_hash": digest("c"),
            }
            for index in range(1, 21)
        ],
    }
    value["release_digest"] = canonical_digest(value)
    return value


class HoldoutReleaseTests(unittest.TestCase):
    def test_valid_sealed_release(self):
        self.assertEqual(validate_release(sealed_release()), [])

    def test_rejects_shared_roles_and_case_content(self):
        value = sealed_release()
        value["roles"]["scoring_session"] = value["roles"]["evaluation_session"]
        value["cases"][0]["symptom"] = "must never enter Git"
        value["release_digest"] = canonical_digest(value)
        self.assertEqual(
            validate_release(value),
            [
                "sealed release custody sessions must be distinct",
                "SA3-HO-001: content keys forbidden: symptom",
                "SA3-HO-001: unexpected keys: symptom",
            ],
        )

    def test_rejects_digest_change(self):
        value = sealed_release()
        value["cases"][0]["family"] = "changed"
        self.assertEqual(validate_release(value), ["release_digest does not match canonical manifest"])

    def test_template_is_valid_and_empty(self):
        template = {
            "schema_version": 1,
            "status": "template",
            "release_id": "sa3-holdout-v1",
            "target_cases": 20,
            "roles": {key: "" for key in ("custodian_session", "review_session", "evaluation_session", "scoring_session")},
            "cases": [],
        }
        self.assertEqual(validate_release(template), [])


if __name__ == "__main__":
    unittest.main()
