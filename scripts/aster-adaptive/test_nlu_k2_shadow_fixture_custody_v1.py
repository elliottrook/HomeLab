import copy
import unittest

import nlu_k2_shadow_fixture_custody_v1 as custody
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


def fixture():
    selected = {}
    for label_id, value in ontology.CATALOGUE.items():
        selected.setdefault(value["request_family"], label_id)
    return [{"id": f"shadow-{family}-{index}",
             "request_text": f"Sanitized fictional {family} request {index}",
             "expected_label_id": selected[family],
             "data_class": "synthetic-sanitized-S0"}
            for family in FAMILIES for index in range(10)]


def seal(rows=None, **changes):
    arguments = dict(development_case_ids=["dev-1"],
                     development_request_sha256=["1" * 64],
                     sealed_case_ids=["sealed-1"],
                     sealed_request_sha256=["2" * 64],
                     custodian_id="fixture-custodian",
                     label_reviewer_id="blind-label-reviewer")
    arguments.update(changes)
    return custody.seal(fixture() if rows is None else rows, **arguments)


class K2ShadowFixtureCustodyTests(unittest.TestCase):
    def test_balanced_private_fixture_emits_content_free_receipt(self):
        rows = fixture(); value = seal(rows)
        self.assertEqual(60, value["case_count"])
        self.assertTrue(value["zero_development_or_sealed_overlap"])
        self.assertFalse(value["effect_authorized"])
        self.assertNotIn(rows[0]["request_text"], repr(value))

    def test_case_or_request_overlap_fails_closed(self):
        rows = fixture(); rows[0]["id"] = "dev-1"
        with self.assertRaisesRegex(ValueError, "overlaps"):
            seal(rows)
        rows = fixture()
        import hashlib
        digest = hashlib.sha256(rows[0]["request_text"].encode()).hexdigest()
        with self.assertRaisesRegex(ValueError, "overlaps"):
            seal(rows, sealed_request_sha256=[digest])

    def test_duplicate_and_unbalanced_fixture_fails_closed(self):
        rows = fixture(); rows[1]["request_text"] = rows[0]["request_text"]
        with self.assertRaises(ValueError): seal(rows)
        rows = fixture(); rows[0]["expected_label_id"] = rows[10]["expected_label_id"]
        with self.assertRaisesRegex(ValueError, "balance"): seal(rows)

    def test_roles_and_data_class_are_fixed(self):
        with self.assertRaisesRegex(ValueError, "roles"):
            seal(custodian_id="same", label_reviewer_id="same")
        rows = fixture(); rows[0]["data_class"] = "personal"
        with self.assertRaisesRegex(ValueError, "data class"): seal(rows)

    def test_unknown_fields_or_labels_fail_closed(self):
        rows = fixture(); rows[0]["extra"] = True
        with self.assertRaises(ValueError): seal(rows)
        rows = fixture(); rows[0]["expected_label_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "label"): seal(rows)


if __name__ == "__main__":
    unittest.main()
