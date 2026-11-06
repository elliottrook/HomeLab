import unittest

import sa4_distinct_canary_plan_v1 as plan_source
import sa4_distinct_canary_transaction_release_v2 as source


class Tests(unittest.TestCase):
    def test_exact_sources_result_and_retained_release(self):
        source.validate_static_evidence()
        source.validate_retained_packet()
        value = source.packet()
        self.assertEqual(3, len(value["installed_source_sha256"]))
        self.assertEqual(4, len(value["release_source_sha256"]))
        self.assertEqual(source.RESULT_SHA256,
                         value["inactive_install_result_sha256"])

    def test_exact_plan_and_fresh_authority(self):
        value = source.packet()
        self.assertEqual(plan_source.PLAN_SHA256, value["plan_sha256"])
        self.assertEqual(source.GRANT_ID,
                         value["required_fresh_authority"]["grant_id"])
        self.assertFalse(
            value["required_fresh_authority"]["prior_approval_reusable"])

    def test_release_is_inert_and_bounded(self):
        value = source.packet()
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["transaction_limits"]["automatic_retry"])
        self.assertFalse(value["transaction_limits"]["service_restart"])
        self.assertEqual("off",
                         value["transaction_limits"]["automatic_routing"])


if __name__ == "__main__":
    unittest.main()
