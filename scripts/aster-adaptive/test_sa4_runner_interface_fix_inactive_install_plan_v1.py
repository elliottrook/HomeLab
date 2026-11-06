import unittest

import sa4_runner_interface_fix_inactive_install_plan_v1 as source


class Tests(unittest.TestCase):
    def test_exact_create_only_correction(self):
        value = source.plan()
        self.assertEqual(2, len(value["changes"]))
        self.assertTrue(all(item["operation"] == "create-exclusive"
                            for item in value["changes"]))
        self.assertFalse(value["effect_authorized"])
        self.assertEqual("off", value["automatic_routing"])

    def test_failed_attempt_is_not_reclassified(self):
        value = source.plan()["failed_attempt"]
        self.assertEqual(1, value["exit_status"])
        self.assertFalse(value["repair_attempted"])
        self.assertFalse(value["grant_claimed"])


if __name__ == "__main__":
    unittest.main()
