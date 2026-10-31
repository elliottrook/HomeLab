import hashlib
import json
import unittest
from pathlib import Path

import nlu_joint_training_private_review_v1 as private_review


SOURCE = Path(__file__).with_name("fixtures") / "nlu-j1-training-draft-v1.json"


def encoded(texts):
    return (json.dumps({
        "cases": [{"id": f"case-{index}", "text": text}
                  for index, text in enumerate(texts)]
    }, sort_keys=True, separators=(",", ":")) + "\n").encode()


def expected(raw):
    texts = {
        private_review.corpus.normalized_text(case["text"])
        for case in json.loads(raw)["cases"]
    }
    return {
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "normalized_text_set_sha256": hashlib.sha256(
            ("\n".join(sorted(texts)) + "\n").encode()
        ).hexdigest(),
        "case_count": len(texts),
    }


class J1PrivateReviewTests(unittest.TestCase):
    def test_content_free_success_builds_one_receipt_per_reference(self):
        raw = {"development-v1": encoded(["A distinct private phrase"])}
        result, receipts = private_review.evaluate(
            SOURCE.read_bytes(), raw,
            expected={"development-v1": expected(raw["development-v1"])},
        )
        self.assertEqual("complete", result["status"])
        self.assertEqual(1, result["receipts_written"])
        self.assertEqual({"development-v1"}, set(receipts))
        self.assertNotIn("private phrase", json.dumps(result).lower())
        self.assertFalse(result["sealed_holdout_read"])

    def test_overlap_is_no_go_and_writes_no_success_receipt(self):
        subject = json.loads(SOURCE.read_text())
        raw = {"calibration-v1": encoded([subject["cases"][0]["text"]])}
        result, receipts = private_review.evaluate(
            SOURCE.read_bytes(), raw,
            expected={"calibration-v1": expected(raw["calibration-v1"])},
        )
        self.assertEqual("no-go", result["status"])
        self.assertEqual(1, result["references"]["calibration-v1"]["overlap_count"])
        self.assertEqual({}, receipts)

    def test_missing_reference_changed_pin_and_holdout_fail_closed(self):
        raw = {"development-v1": encoded(["A distinct private phrase"])}
        with self.assertRaises(ValueError):
            private_review.evaluate(SOURCE.read_bytes(), raw, expected={})
        changed = expected(raw["development-v1"])
        changed["case_count"] = 2
        with self.assertRaises(ValueError):
            private_review.evaluate(
                SOURCE.read_bytes(), raw, expected={"development-v1": changed}
            )
        with_holdout = dict(raw)
        with_holdout["sealed-holdout"] = encoded(["Do not read this"])
        with self.assertRaises(ValueError):
            private_review.evaluate(
                SOURCE.read_bytes(), with_holdout,
                expected={"development-v1": expected(raw["development-v1"])},
            )

    def test_subject_is_exactly_bound(self):
        changed = SOURCE.read_bytes().replace(b"Please repair", b"Please alter", 1)
        raw = {"development-v1": encoded(["A distinct private phrase"])}
        with self.assertRaises(ValueError):
            private_review.evaluate(
                changed, raw,
                expected={"development-v1": expected(raw["development-v1"])},
            )


if __name__ == "__main__":
    unittest.main()
