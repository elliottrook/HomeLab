import unittest

import nlu_k2_shortlist_arbitration_preregistration_v1 as source


class K2PreregistrationTests(unittest.TestCase):
    def test_exact_manifest_is_non_authorizing(self):
        result = source.validate(source.MANIFEST)
        self.assertEqual(4, result["candidate_count"])
        self.assertEqual(192, result["development_model_requests"])
        self.assertTrue(result["b60_booking_required"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_duplicate_and_noncanonical_json_fail_closed(self):
        with self.assertRaises(ValueError):
            source.validate(b'{"schema":"one","schema":"two"}\n')
        with self.assertRaises(ValueError):
            source.validate(source.MANIFEST.rstrip(b"\n"))

    def test_shortlister_cannot_become_final_decider(self):
        value = source.expected()
        value["shortlister"]["may_make_final_decision"] = True
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))

    def test_validation_cannot_repair_prompt_or_threshold(self):
        value = source.expected()
        value["development_gate"]["prompt_or_threshold_repair"] = "allowed"
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))
        value = source.expected()
        value["acceptance"]["threshold_repair_after_results"] = "allowed"
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))

    def test_model_effect_boundaries_are_fixed(self):
        for section, field, changed in (
            ("arbitrator", "retries", 1),
            ("arbitrator", "tools", "allowed"),
            ("runtime_admission", "service_restart", "allowed"),
            ("runtime_admission", "model_or_backend_change", "allowed"),
        ):
            value = source.expected()
            value[section][field] = changed
            with self.assertRaises(ValueError):
                source.validate(source.canonical(value))

    def test_sealed_evaluation_cannot_open_early(self):
        value = source.expected()
        value["sealed_evaluation"]["access_before_development_pass"] = "allowed"
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))


if __name__ == "__main__":
    unittest.main()
