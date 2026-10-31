import copy
import json
import unittest

import nlu_joint_training_nonoverlap_receipt_v1 as receipt


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def value(reference_class):
    reference = receipt.REFERENCES[reference_class]
    result = {
        "schema": receipt.SCHEMA,
        "reference_class": reference_class,
        "subject_source_sha256": "1" * 64,
        "subject_normalized_text_set_sha256": "2" * 64,
        "subject_case_count": 400,
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


def complete_set():
    return {name: encoded(value(name)) for name in receipt.REFERENCES}


class J1NonoverlapReceiptTests(unittest.TestCase):
    def test_complete_exact_set_is_accepted(self):
        values, errors = receipt.validate_set(complete_set())
        self.assertEqual([], errors)
        self.assertEqual(set(receipt.REFERENCES), set(values))

    def test_missing_or_extra_reference_fails(self):
        missing = complete_set()
        missing.pop("calibration-v6")
        self.assertTrue(receipt.validate_set(missing)[1])
        extra = complete_set()
        extra["sealed-holdout"] = b"{}\n"
        self.assertTrue(receipt.validate_set(extra)[1])

    def test_reference_overlap_authority_and_reviewer_fail(self):
        for field, changed in (
            ("overlap_count", 1),
            ("authority", "granted"),
            ("reviewer", "corpus-custodian"),
            ("reference_case_count", 59),
        ):
            values = complete_set()
            item = value("calibration-v3")
            item[field] = changed
            item["receipt_sha256"] = receipt.canonical_sha256(item)
            values["calibration-v3"] = encoded(item)
            with self.subTest(field=field):
                self.assertTrue(receipt.validate_set(values)[1])

    def test_subject_identity_must_match_across_receipts(self):
        values = complete_set()
        item = value("calibration-v4")
        item["subject_source_sha256"] = "3" * 64
        item["receipt_sha256"] = receipt.canonical_sha256(item)
        values["calibration-v4"] = encoded(item)
        self.assertTrue(any("one subject" in error for error in receipt.validate_set(values)[1]))

    def test_duplicate_key_and_self_hash_fail(self):
        values = complete_set()
        values["development-v1"] = values["development-v1"].replace(
            b'"schema":"aster-nlu-j1-nonoverlap-receipt.v1"',
            b'"schema":"aster-nlu-j1-nonoverlap-receipt.v1","schema":"duplicate"',
        )
        self.assertTrue(receipt.validate_set(values)[1])
        changed = complete_set()
        item = value("calibration-v2")
        item["receipt_sha256"] = "0" * 64
        changed["calibration-v2"] = encoded(item)
        self.assertTrue(receipt.validate_set(changed)[1])


if __name__ == "__main__":
    unittest.main()
