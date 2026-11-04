import copy
import unittest

import nlu_j2_owner_acceptance_v1 as acceptance


class J2OwnerAcceptanceTests(unittest.TestCase):
    def test_exact_release_only_acceptance_validates(self):
        value = acceptance.accepted_record("jason-owner")
        result = acceptance.validate(acceptance.canonical(value))
        self.assertEqual("corpus-release-only", result["scope"])
        self.assertFalse(result["training_authorized"])
        self.assertFalse(result["sealed_evaluation_access"])

    def test_hash_scope_or_authority_drift_fails_closed(self):
        source = acceptance.accepted_record("jason-owner")
        variants = []
        for field, changed in (
                ("corpus_sha256", "a" * 64),
                ("normalized_text_set_sha256", "b" * 64),
                ("label_review_sha256", "c" * 64),
                ("quality_review_sha256", "d" * 64),
                ("scope", "training"),
                ("training_authorized", True),
                ("sealed_evaluation_access", True),
                ("authority", "granted"),
                ("automatic_routing", "on")):
            value = copy.deepcopy(source)
            value[field] = changed
            value["receipt_sha256"] = acceptance.receipt_sha256(value)
            variants.append(value)
        for value in variants:
            with self.subTest(value=value), self.assertRaises(ValueError):
                acceptance.validate(acceptance.canonical(value))

    def test_missing_owner_or_stale_self_hash_fails(self):
        with self.assertRaises(ValueError):
            acceptance.accepted_record("")
        value = acceptance.accepted_record("jason-owner")
        value["owner_id"] = "changed-owner"
        with self.assertRaises(ValueError):
            acceptance.validate(acceptance.canonical(value))


if __name__ == "__main__":
    unittest.main()

