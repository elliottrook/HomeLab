import unittest
import sa4_first_repair_transaction_release_v6 as release
class Tests(unittest.TestCase):
    def test_runner_and_all_sources_bound(self):
        release.validate_static_evidence(); release.validate_retained_packet(); value=release.packet(); self.assertEqual(9,len(value["installed_source_sha256"])); self.assertEqual(release.RUNNER_RESULT_SHA256,value["fixed_runner_install_result_sha256"])
    def test_fresh_authority_only(self):
        value=release.packet(); self.assertFalse(value["required_fresh_authority"]["prior_approval_reusable"]); self.assertEqual("new-unique-v6-id",value["required_fresh_authority"]["grant_id"])
    def test_inert_limits(self):
        value=release.packet(); self.assertFalse(value["effect_authorized"]); self.assertFalse(value["transaction_limits"]["automatic_retry"]); self.assertEqual("installed-no-argument-entry-point",value["required_fresh_runtime"]["fixed_runner"])
if __name__=="__main__": unittest.main()
