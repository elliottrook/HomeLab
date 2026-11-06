import unittest

import sa4_distinct_canary_authority_packet_v2 as authority
import sa4_distinct_canary_plan_v1 as plan
import sa4_distinct_canary_transaction_release_v3 as source


class Tests(unittest.TestCase):
    def test_release_is_fresh_path_and_effect_gated(self):
        value = source.packet()
        self.assertEqual(plan.PLAN_SHA256, value["plan_sha256"])
        self.assertEqual(authority.GRANT_ID,
                         value["required_fresh_authority"]["grant_id"])
        self.assertEqual("/var/lib/aster/sa4/transaction-input-v3",
                         value["runtime_paths"]["input"])
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["failed_predecessor"]["reusable"])

    def test_retained_packet_is_exact(self):
        source.validate_retained_packet()


if __name__ == "__main__":
    unittest.main()
