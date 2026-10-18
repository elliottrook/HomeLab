import unittest

from full_inference_lab_install_preflight import validate_imports


class FullInferenceInstallPreflightTests(unittest.TestCase):
    def test_import_and_command_contract_is_no_effect(self):
        value = validate_imports()
        self.assertEqual(value["modules"], 8)
        self.assertEqual(value["drain_effects"], 5)
        self.assertEqual(value["restore_effects"], 10)
        self.assertEqual(value["effects"], "not-attempted")


if __name__ == "__main__":
    unittest.main()
