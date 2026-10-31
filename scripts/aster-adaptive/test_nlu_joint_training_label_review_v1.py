import copy
import json
import unittest
from pathlib import Path

import nlu_joint_training_label_review_v1 as review


SOURCE = Path(__file__).with_name("fixtures") / "nlu-j1-training-draft-v1.json"


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def complete():
    source = json.loads(SOURCE.read_text())
    value = review.template(SOURCE.read_bytes())
    labels = {case["id"]: case["label_id"] for case in source["cases"]}
    for row in value["rows"]:
        row["status"] = "accepted"
        row["reviewed_label_id"] = labels[row["id"]]
    value["review_sha256"] = review.canonical_sha256(value)
    return value


class J1LabelReviewTests(unittest.TestCase):
    def test_complete_independent_review_is_release_eligible(self):
        summary = review.validate(SOURCE.read_bytes(), encoded(complete()))
        self.assertEqual(400, summary["reviewed"])
        self.assertEqual(400, summary["accepted"])
        self.assertEqual(0, summary["corrected"])
        self.assertTrue(summary["release_eligible"])

    def test_explicit_correction_is_valid_but_not_release_eligible(self):
        value = complete()
        original = value["rows"][0]["reviewed_label_id"]
        replacement = next(label for label in sorted(__import__(
            "nlu_whole_label_choice_v1").CATALOGUE) if label != original)
        value["rows"][0].update(status="corrected", reviewed_label_id=replacement)
        value["review_sha256"] = review.canonical_sha256(value)
        summary = review.validate(SOURCE.read_bytes(), encoded(value))
        self.assertEqual(1, summary["corrected"])
        self.assertFalse(summary["release_eligible"])

    def test_pending_duplicate_authority_and_self_hash_fail(self):
        variants = []
        pending = complete()
        pending["rows"][0]["status"] = "pending"
        pending["review_sha256"] = review.canonical_sha256(pending)
        variants.append(pending)
        duplicate = complete()
        duplicate["rows"][1]["id"] = duplicate["rows"][0]["id"]
        duplicate["review_sha256"] = review.canonical_sha256(duplicate)
        variants.append(duplicate)
        authority = complete()
        authority["authority"] = "granted"
        authority["review_sha256"] = review.canonical_sha256(authority)
        variants.append(authority)
        bad_hash = complete()
        bad_hash["review_sha256"] = "0" * 64
        variants.append(bad_hash)
        for value in variants:
            with self.subTest(), self.assertRaises(ValueError):
                review.validate(SOURCE.read_bytes(), encoded(value))

    def test_template_is_unscored_and_source_bound(self):
        value = review.template(SOURCE.read_bytes())
        self.assertTrue(all(row["status"] == "pending" for row in value["rows"]))
        self.assertEqual(review.SOURCE_SHA256, value["source_sha256"])


if __name__ == "__main__":
    unittest.main()
