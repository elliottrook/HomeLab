import copy
import json
import unittest

import nlu_nonoverlap_receipt as receipt


def value(reference_class="development"):
    reference = receipt.REFERENCES[reference_class]
    result = {
        "schema": receipt.SCHEMA,
        "reference_class": reference_class,
        "subject_source_sha256": "1" * 64,
        "subject_normalized_text_set_sha256": "2" * 64,
        "subject_case_count": 36,
        "reference_artifact_sha256": reference["artifact_sha256"],
        "reference_normalized_text_set_sha256": reference["normalized_text_set_sha256"],
        "reference_case_count": reference["case_count"],
        "overlap_count": 0,
        "reviewer": receipt.REVIEWER,
        "authority": "not-granted",
        "receipt_sha256": "",
    }
    result["receipt_sha256"] = receipt.canonical_sha256(result)
    return result


def encoded(item):
    return (json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n").encode()


class NonoverlapReceiptTests(unittest.TestCase):
    def test_both_exact_references_are_valid(self):
        for reference_class in receipt.REFERENCES:
            with self.subTest(reference_class=reference_class):
                self.assertEqual([], receipt.validate_receipt(value(reference_class)))

    def test_overlap_reference_drift_and_authority_fail_closed(self):
        changes = [
            ("overlap_count", 1),
            ("reference_case_count", 23),
            ("authority", "granted"),
            ("reviewer", "case-custodian"),
        ]
        for key, changed in changes:
            item = value()
            item[key] = changed
            item["receipt_sha256"] = receipt.canonical_sha256(item)
            with self.subTest(key=key):
                self.assertTrue(receipt.validate_receipt(item))

    def test_self_hash_and_unique_json_are_required(self):
        item = value()
        item["receipt_sha256"] = "0" * 64
        self.assertIn(
            "non-overlap receipt_sha256 does not match canonical receipt",
            receipt.validate_receipt(item),
        )
        duplicate = encoded(value()).replace(
            b'"schema":"aster-nlu-nonoverlap-receipt.v1"',
            b'"schema":"aster-nlu-nonoverlap-receipt.v1","schema":"duplicate"',
        )
        _, errors = receipt.load_and_validate(duplicate, "development")
        self.assertTrue(any("unique-key" in error for error in errors))

    def test_reference_class_is_bound(self):
        item = value("calibration")
        self.assertIn(
            "non-overlap receipt reference class changed",
            receipt.validate_receipt(item, "development"),
        )


if __name__ == "__main__":
    unittest.main()
