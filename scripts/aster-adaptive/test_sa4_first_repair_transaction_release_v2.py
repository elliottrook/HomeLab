import unittest

import sa4_first_repair_transaction_release_v2 as release


class SA4FirstRepairTransactionReleaseV2Tests(unittest.TestCase):
    def test_superseded_source_drift_is_detected(self):
        with self.assertRaises(ValueError): release.validate_sources()
        self.assertEqual(4, len(release.SOURCES))

    def test_release_requires_new_authority_and_runtime_controls(self):
        value = release.packet()
        self.assertEqual("new-exact-plan-detached-proof",
                         value["required_fresh_authority"]["owner"])
        self.assertEqual("new-exact-plan-one-use-grant-and-proof",
                         value["required_fresh_authority"]["ai_pam"])
        self.assertTrue(value["required_runtime"]["fresh_measurement"])
        self.assertTrue(value["required_runtime"]["exclusive_checkpoint"])

    def test_release_has_no_effect_or_retry(self):
        value = release.packet()
        self.assertEqual("superseded-no-go-runtime-controls-not-owned",
                         value["status"])
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["transaction_limits"]["automatic_retry"])
        self.assertEqual(1, value["transaction_limits"]["maximum_repairs"])
        self.assertEqual(1, value["transaction_limits"]["maximum_rollbacks"])
        self.assertEqual("off", value["transaction_limits"]["automatic_routing"])


if __name__ == "__main__":
    unittest.main()
