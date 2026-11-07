import copy
import unittest

import nlu_k2_sealed_transaction_preregistration_v1 as prereg


class K2SealedTransactionPreregistrationTests(unittest.TestCase):
    def test_exact_contract_is_non_authorizing(self):
        value = prereg.artifact()
        summary = prereg.validate(value)
        self.assertEqual(11, summary["runtime_pins"])
        self.assertEqual(32, summary["model_requests"])
        self.assertFalse(summary["effect_authorized"])
        self.assertFalse(value["effect"]["tools"])
        self.assertFalse(value["effect"]["route_effect"])
        self.assertEqual("off", value["automatic_routing"])

    def test_requires_restored_development_pass(self):
        for field, changed in (("development_gate_passed", False),
                               ("production_restored", False),
                               ("development_status", "reject")):
            value = copy.deepcopy(prereg.artifact())
            value["prerequisite"][field] = changed
            with self.assertRaises(ValueError):
                prereg.validate(value)

    def test_network_contract_uses_only_existing_control_direction(self):
        network = prereg.artifact()["network"]
        self.assertEqual("mac-mini-to-macbook-existing-ssh",
                         network["control_direction"])
        self.assertFalse(network["direct_macbook_b60"])
        self.assertFalse(network["new_access_grant"])
        self.assertFalse(network["standing_b60_credential_on_macbook"])

    def test_success_requires_complete_teardown_and_restoration(self):
        success = prereg.artifact()["success"]
        for key in ("production_restored", "lease_ready", "locks_absent",
                    "tunnels_absent", "relay_absent", "runner_absent",
                    "private_listener_absent"):
            self.assertTrue(success[key])

    def test_booking_identity_is_bounded(self):
        good = "aster-stream-a-m3-k2-sealed-20261107-1200-r1"
        self.assertEqual(good, prereg.validate_booking_id(good))
        for bad in (good + "-extra", "m3-k2-sealed", "../../booking"):
            with self.assertRaises(ValueError):
                prereg.validate_booking_id(bad)


if __name__ == "__main__":
    unittest.main()
