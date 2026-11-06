import hashlib
import unittest

import sa4_distinct_canary_plan_v2 as plan
import sa4_distinct_canary_transaction_release_v5 as source


class ReleaseTests(unittest.TestCase):
    def test_unique_checkpoint_and_fresh_paths(self):
        value = source.packet()
        self.assertEqual(plan.PLAN_SHA256, value["plan_sha256"])
        self.assertEqual(plan.PLAN_ID, value["plan_id"])
        self.assertTrue(value["runtime_paths"]["checkpoint"].endswith(
            "sa4-canary-v2-second-repair-v1.original"))
        self.assertIn("transaction-input-v5", value["runtime_paths"]["input"])
        self.assertFalse(value["effect_authorized"])
        self.assertFalse(value["transaction_limits"]["automatic_retry"])

    def test_packet_is_canonical(self):
        raw = source.canonical()
        self.assertEqual(raw, source.canonical())
        self.assertEqual(64, len(hashlib.sha256(raw).hexdigest()))


if __name__ == "__main__":
    unittest.main()
