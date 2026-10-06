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

    def test_rejects_top_level_content_even_with_valid_digest(self):
        value = sealed_release()
        value['prompts'] = ['synthetic content that must not be published']
        value['release_digest'] = canonical_digest(value)
        self.assertIn('unexpected top-level fields; content is forbidden', validate_release(value))

    def test_malformed_types_fail_closed_without_crashing(self):
        self.assertEqual(validate_release([]), ['release must be an object'])
        value = sealed_release()
        value['roles']['custodian_session'] = []
        value['cases'][0]['id'] = []
        value['cases'][0]['case_hash'] = 123
        value['release_digest'] = 456
        errors = validate_release(value)
        self.assertIn('every case requires an id', errors)
        self.assertIn('sealed release requires all custody sessions', errors)
        self.assertIn('sealed release requires a SHA-256 release_digest', errors)


if __name__ == "__main__":
    unittest.main()
