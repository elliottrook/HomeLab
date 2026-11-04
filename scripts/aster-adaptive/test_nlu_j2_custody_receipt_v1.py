import copy
import unittest

import nlu_j2_custody_receipt_v1 as custody


def receipt(value):
    value = copy.deepcopy(value)
    value["receipt_sha256"] = custody._digest(value)
    return custody.canonical(value)


CORPUS = {
    "schema": "aster-nlu-j2-corpus-custody.v1",
    "manifest_sha256": custody.MANIFEST_SHA256,
    "custodian_id": "corpus-custodian",
    "reviewer_id": "label-reviewer",
    "corpus_sha256": "a" * 64,
    "normalized_text_set_sha256": "b" * 64,
    "label_review_sha256": "c" * 64,
    "quality_review_sha256": "f" * 64,
    "train_rows": 768, "validation_rows": 192, "labels": 16,
    "overlap_reference_count": 8, "normalized_overlap": 0,
    "content_in_receipt": False, "authority": "not-granted",
}
EVALUATION = {
    "schema": "aster-nlu-j2-evaluation-seal.v1",
    "manifest_sha256": custody.MANIFEST_SHA256,
    "custodian_id": "evaluation-custodian",
    "evaluation_sha256": "d" * 64,
    "normalized_text_set_sha256": "e" * 64,
    "cases": 32, "labels": 16, "cases_per_label": 2,
    "sealed_before_training": True, "trainer_access": "forbidden",
    "content_in_receipt": False, "authority": "not-granted",
}


class J2CustodyReceiptTests(unittest.TestCase):
    def test_three_distinct_content_free_roles_admit_source_only(self):
        value = custody.admit(receipt(CORPUS), receipt(EVALUATION))
        self.assertTrue(value["roles_distinct"])
        self.assertFalse(value["training_authorized"])
        self.assertEqual("not-granted", value["authority"])

    def test_corpus_counts_overlap_and_content_fail_closed(self):
        for field, changed in (("train_rows", 767), ("normalized_overlap", 1),
                               ("content_in_receipt", True)):
            value = copy.deepcopy(CORPUS); value[field] = changed
            with self.assertRaises(ValueError):
                custody.corpus_receipt(receipt(value))

    def test_corpus_custodian_cannot_self_review(self):
        value = copy.deepcopy(CORPUS); value["reviewer_id"] = value["custodian_id"]
        with self.assertRaisesRegex(ValueError, "distinct"):
            custody.corpus_receipt(receipt(value))

    def test_evaluation_must_be_balanced_sealed_and_unseen(self):
        for field, changed in (("cases", 31), ("cases_per_label", 1),
                               ("sealed_before_training", False),
                               ("trainer_access", "allowed")):
            value = copy.deepcopy(EVALUATION); value[field] = changed
            with self.assertRaises(ValueError):
                custody.evaluation_receipt(receipt(value))

    def test_all_three_roles_must_be_distinct(self):
        value = copy.deepcopy(EVALUATION); value["custodian_id"] = CORPUS["reviewer_id"]
        with self.assertRaisesRegex(ValueError, "not distinct"):
            custody.admit(receipt(CORPUS), receipt(value))

    def test_receipts_must_bind_preregistration(self):
        value = copy.deepcopy(CORPUS); value["manifest_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "preregistration"):
            custody.corpus_receipt(receipt(value))

    def test_self_hash_and_duplicate_keys_fail_closed(self):
        raw = receipt(CORPUS).replace(b'"train_rows":768', b'"train_rows":769')
        with self.assertRaisesRegex(ValueError, "self-hash"):
            custody.corpus_receipt(raw)
        with self.assertRaises(ValueError):
            custody.corpus_receipt(b'{"schema":"x","schema":"y"}')


if __name__ == "__main__":
    unittest.main()
