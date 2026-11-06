import unittest

import sa4_first_repair_transaction_release_v3 as release


class SA4FirstRepairTransactionReleaseV3Tests(unittest.TestCase):
    def test_corrected_sources_are_exact(self):
        release.validate_sources()
        self.assertEqual(2, len(release.SOURCES))

    def test_controls_are_owned_not_claimed(self):
        value = release.packet()["runtime_control_correction"]
        self.assertTrue(value["real_lock_owned"])
        self.assertTrue(value["operator_stop_owned"])
        self.assertTrue(value["caller_supplied_control_claim_rejected"])
        self.assertTrue(value["uncertainty_retains_state"])

    def test_candidate_remains_inactive(self):
        value = release.packet()
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["transaction_limits"]["automatic_retry"])
        self.assertEqual("candidate-pending-inactive-runtime-control-install",
                         value["status"])


if __name__ == "__main__":
    unittest.main()
