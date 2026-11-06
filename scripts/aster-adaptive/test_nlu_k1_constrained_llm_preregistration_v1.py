import unittest

import nlu_k1_constrained_llm_preregistration_v1 as source


class Tests(unittest.TestCase):
    def test_exact_manifest(self):
        result = source.validate(source.MANIFEST)
        self.assertTrue(result["materially_distinct"])
        self.assertTrue(result["b60_booking_required"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):
            source.validate(b'{"schema":"one","schema":"two"}\n')

    def test_noncanonical_manifest_rejected(self):
        with self.assertRaises(ValueError):
            source.validate(source.MANIFEST.rstrip(b"\n"))

    def test_model_change_or_training_rejected(self):
        value = source.expected()
        value["model_boundary"]["replacement"] = True
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))
        value = source.expected()
        value["material_change"]["training"] = True
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))

    def test_prompt_and_eval_repair_rejected(self):
        value = source.expected()
        value["prompt_contract"]["free_text"] = "allowed"
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))
        value = source.expected()
        value["development_gate"]["prompt_repair_after_results"] = "allowed"
        with self.assertRaises(ValueError):
            source.validate(source.canonical(value))


if __name__ == "__main__":
    unittest.main()
