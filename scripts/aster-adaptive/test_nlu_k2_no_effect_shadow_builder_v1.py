import copy
import unittest

import nlu_k2_no_effect_shadow_builder_v1 as builder
import nlu_k2_no_effect_shadow_v1 as shadow
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


def rows():
    selected = {}
    for label_id, value in ontology.CATALOGUE.items():
        selected.setdefault(value["request_family"], label_id)
    assert set(selected) == set(FAMILIES)
    output = []
    for family in FAMILIES:
        label_id = selected[family]
        for index in range(10):
            output.append({
                "id": f"s0-{family}-{index}",
                "request_text": f"Sanitized representative {family} request {index}",
                "expected_label_id": label_id, "final_label_id": label_id,
                "candidate_accepted": True, "baseline_status": "local",
                "latency_seconds": 2.5,
            })
    return output


class K2NoEffectShadowBuilderTests(unittest.TestCase):
    def test_exact_balanced_rows_build_a_passing_no_effect_envelope(self):
        value = builder.build(rows())
        score = shadow.validate(value)
        self.assertEqual(60, score["accepted"])
        self.assertEqual(60, score["accepted_exact"])
        self.assertTrue(score["shadow_gate_passed"])
        self.assertFalse(score["route_execution_attempted"])

    def test_request_text_is_reduced_to_digest(self):
        source = rows(); secret = source[0]["request_text"]
        value = builder.build(source)
        self.assertNotIn("request_text", value["cases"][0])
        self.assertNotIn(secret, repr(value))
        self.assertEqual(64, len(value["cases"][0]["request_sha256"]))

    def test_duplicate_or_unbalanced_rows_fail_closed(self):
        source = rows(); source[1]["id"] = source[0]["id"]
        with self.assertRaises(ValueError): builder.build(source)
        source = rows(); source[0]["expected_label_id"] = source[10]["expected_label_id"]
        with self.assertRaisesRegex(ValueError, "balance"): builder.build(source)

    def test_unknown_fields_labels_or_effect_claims_fail_closed(self):
        source = rows(); source[0]["extra"] = True
        with self.assertRaises(ValueError): builder.build(source)
        source = rows(); source[0]["final_label_id"] = "missing"
        with self.assertRaises(ValueError): builder.build(source)
        value = builder.build(rows()); value["route_execution_attempted"] = True
        value["release_sha256"] = shadow.release_sha256(value)
        with self.assertRaises(ValueError): shadow.validate(value)


if __name__ == "__main__":
    unittest.main()
