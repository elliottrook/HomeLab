import copy
import unittest

import nlu_k2_shadow_fixture_preregistration_v1 as preregistration


class K2ShadowFixturePreregistrationTests(unittest.TestCase):
    def test_exact_fixture_is_balanced_private_and_non_authorizing(self):
        value = preregistration.artifact(); result = preregistration.validate(value)
        self.assertEqual(60, result["cases"])
        self.assertEqual(10, result["cases_per_family"])
        self.assertTrue(result["independent_label_review_required"])
        self.assertFalse(result["effect_authorized"])
        self.assertEqual("off", result["automatic_routing"])

    def test_existing_development_and_sealed_identities_are_explicit(self):
        independence = preregistration.artifact()["independence"]
        self.assertEqual(64, len(independence["development_corpus_sha256"]))
        self.assertEqual(64, len(independence["sealed_evaluation_sha256"]))
        self.assertTrue(independence["zero_text_or_case_id_overlap_with_development"])
        self.assertTrue(independence["zero_text_or_case_id_overlap_with_sealed_evaluation"])

    def test_label_review_precedes_and_is_blind_to_candidate_collection(self):
        independence = preregistration.artifact()["independence"]
        self.assertTrue(independence["fixture_custodian_and_label_reviewer_distinct"])
        self.assertTrue(independence["case_labels_reviewed_before_candidate_collection"])
        self.assertTrue(independence["candidate_output_hidden_from_label_reviewer"])

    def test_weakened_independence_privacy_or_effect_fails_closed(self):
        for mutate in (
            lambda value: value["independence"].update(
                zero_text_or_case_id_overlap_with_sealed_evaluation=False),
            lambda value: value["fixture"].update(personal_or_secret_material=True),
            lambda value: value["collection"].update(route_execution=True),
            lambda value: value.update(automatic_routing="on"),
        ):
            value = copy.deepcopy(preregistration.artifact()); mutate(value)
            with self.assertRaises(ValueError): preregistration.validate(value)


if __name__ == "__main__":
    unittest.main()
