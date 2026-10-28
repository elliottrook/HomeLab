import unittest

from full_inference_lab_install_preflight import validate_imports
from full_inference_lab_runtime import main as runtime_main


class FullInferenceInstallPreflightTests(unittest.TestCase):
    def test_import_and_command_contract_is_no_effect(self):
        value = validate_imports()
        self.assertEqual(value["modules"], 10)
        self.assertEqual(value["drain_effects"], 7)
        self.assertEqual(value["restore_effects"], 14)
        self.assertEqual(value["effects"], "not-attempted")

    def test_pinned_runtime_entrypoint_is_default_deny(self):
        self.assertEqual(runtime_main(["--phase", "start", "--owner-id", "owner-1"]), 0)

    def test_combined_pilot_entrypoint_is_default_deny(self):
        self.assertEqual(runtime_main(["--phase", "pilot", "--owner-id", "owner-1"]), 0)


if __name__ == "__main__":
    unittest.main()
