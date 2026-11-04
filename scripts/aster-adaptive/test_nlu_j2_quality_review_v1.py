import copy
import json
import unittest

import nlu_j2_quality_review_v1 as quality
from test_nlu_j2_corpus_release_v1 import encoded, source


def complete(source_raw):
    value = quality.template(source_raw)
    for row in value["rows"]:
        row["judgments"] = {dimension: True for dimension in quality.DIMENSIONS}
    value["review_sha256"] = quality.review_sha256(value)
    return encoded(value)


class J2QualityReviewTests(unittest.TestCase):
    def test_complete_exact_review_is_release_eligible(self):
        raw = source()
        summary = quality.validate(raw, complete(raw))
        self.assertEqual(960, summary["reviewed"])
        self.assertTrue(summary["release_eligible"])
        self.assertEqual(0, summary["naturalness_failures"])
        self.assertEqual("not-granted", summary["authority"])

    def test_pending_or_unexplained_failure_is_rejected(self):
        raw = source()
        value = json.loads(complete(raw))
        value["rows"][0]["judgments"]["grammar"] = None
        value["review_sha256"] = quality.review_sha256(value)
        with self.assertRaises(ValueError):
            quality.validate(raw, encoded(value))
        value = json.loads(complete(raw))
        value["rows"][0]["judgments"]["grammar"] = False
        value["review_sha256"] = quality.review_sha256(value)
        with self.assertRaisesRegex(ValueError, "notes"):
            quality.validate(raw, encoded(value))

    def test_explained_failure_is_valid_but_not_release_eligible(self):
        raw = source()
        value = json.loads(complete(raw))
        value["rows"][0]["judgments"]["naturalness"] = False
        value["rows"][0]["notes"] = "Awkward synthetic phrasing."
        value["review_sha256"] = quality.review_sha256(value)
        summary = quality.validate(raw, encoded(value))
        self.assertFalse(summary["release_eligible"])
        self.assertEqual(1, summary["naturalness_failures"])

    def test_source_or_self_hash_drift_fails_closed(self):
        raw = source()
        value = json.loads(complete(raw))
        value["source_sha256"] = "a" * 64
        value["review_sha256"] = quality.review_sha256(value)
        with self.assertRaises(ValueError):
            quality.validate(raw, encoded(value))
        value = json.loads(complete(raw))
        value["rows"][0]["id"] = value["rows"][1]["id"]
        value["review_sha256"] = quality.review_sha256(value)
        with self.assertRaises(ValueError):
            quality.validate(raw, encoded(value))


if __name__ == "__main__":
    unittest.main()
