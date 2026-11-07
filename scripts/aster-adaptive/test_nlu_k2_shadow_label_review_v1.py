import copy
import unittest

import nlu_k2_shadow_fixture_custody_v1 as custody
import nlu_k2_shadow_label_review_v1 as reviewer
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


def records():
    selected = {}
    for label_id, value in ontology.CATALOGUE.items():
        selected.setdefault(value["request_family"], label_id)
    return [{"id": f"shadow-{family}-{index}",
             "request_text": f"Sanitized fictional {family} request {index}",
             "expected_label_id": selected[family],
             "data_class": "synthetic-sanitized-S0"}
            for family in FAMILIES for index in range(10)]


def inputs():
    source = records()
    receipt = custody.seal(source, development_case_ids=["dev"],
        development_request_sha256=["1" * 64], sealed_case_ids=["sealed"],
        sealed_request_sha256=["2" * 64], custodian_id="custodian",
        label_reviewer_id="reviewer")
    labels = [{"id": row["id"], "expected_label_id": row["expected_label_id"]}
              for row in source]
    return receipt, labels


class K2ShadowLabelReviewTests(unittest.TestCase):
    def test_matching_blind_labels_pass_content_free(self):
        receipt, labels = inputs()
        value = reviewer.review(receipt, labels, reviewer_id="reviewer",
                                candidate_output_present=False)
        self.assertTrue(value["independent_label_review_passed"])
        self.assertFalse(value["candidate_output_observed"])
        self.assertNotIn(records()[0]["request_text"], repr(value))

    def test_reviewer_must_match_and_remain_distinct(self):
        receipt, labels = inputs()
        with self.assertRaisesRegex(ValueError, "reviewer"):
            reviewer.review(receipt, labels, reviewer_id="other",
                            candidate_output_present=False)
        receipt["custodian_id_sha256"] = receipt["label_reviewer_id_sha256"]
        with self.assertRaisesRegex(ValueError, "reviewer"):
            reviewer.review(receipt, labels, reviewer_id="reviewer",
                            candidate_output_present=False)

    def test_candidate_output_must_not_exist(self):
        receipt, labels = inputs()
        with self.assertRaisesRegex(ValueError, "precede"):
            reviewer.review(receipt, labels, reviewer_id="reviewer",
                            candidate_output_present=True)

    def test_changed_labels_or_ids_fail_closed(self):
        receipt, labels = inputs(); labels[0]["expected_label_id"] = labels[10]["expected_label_id"]
        with self.assertRaises(ValueError):
            reviewer.review(receipt, labels, reviewer_id="reviewer",
                            candidate_output_present=False)
        receipt, labels = inputs(); labels[0]["id"] = "changed"
        with self.assertRaises(ValueError):
            reviewer.review(receipt, labels, reviewer_id="reviewer",
                            candidate_output_present=False)

    def test_changed_receipt_or_unknown_fields_fail_closed(self):
        receipt, labels = inputs(); receipt["effect_authorized"] = True
        with self.assertRaisesRegex(ValueError, "receipt"):
            reviewer.review(receipt, labels, reviewer_id="reviewer",
                            candidate_output_present=False)
        receipt, labels = inputs(); labels[0]["extra"] = True
        with self.assertRaisesRegex(ValueError, "fields"):
            reviewer.review(receipt, labels, reviewer_id="reviewer",
                            candidate_output_present=False)


if __name__ == "__main__":
    unittest.main()
