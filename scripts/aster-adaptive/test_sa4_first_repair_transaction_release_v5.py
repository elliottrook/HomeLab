import unittest
import sa4_first_repair_transaction_release_v5 as release

class Tests(unittest.TestCase):
    def test_static_evidence(self):
        release.validate_static_evidence(); release.validate_retained_packet(); self.assertEqual(8,len(release.SOURCES))
    def test_controller_is_bound(self):
        value=release.packet(); self.assertEqual(release.CONTROLLER_RESULT_SHA256,value["effect_controller_install_result_sha256"])
        self.assertEqual("fixed-controller-bridge-protocol",value["required_fresh_runtime"]["observer_exchange"])
    def test_fresh_authority_only(self):
        value=release.packet()["required_fresh_authority"]
        self.assertFalse(value["prior_approval_reusable"]); self.assertEqual("new-unique-v5-id",value["grant_id"])
    def test_limits(self):
        value=release.packet(); self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["transaction_limits"]["automatic_retry"]); self.assertFalse(value["transaction_limits"]["service_restart"])
        self.assertEqual((1,2),(value["transaction_limits"]["observer_signatures_success"],value["transaction_limits"]["observer_signatures_rollback"]))

if __name__=="__main__": unittest.main()
