import unittest

import sa4_distinct_canary_authority_packet_v3 as authority
import sa4_distinct_canary_transaction_release_v4 as source


class Tests(unittest.TestCase):
    def test_release_is_corrected_and_fresh(self):
        value = source.packet()
        self.assertEqual(authority.GRANT_ID,
                         value["required_fresh_authority"]["grant_id"])
        self.assertEqual("/var/lib/aster/sa4/transaction-input-v4",
                         value["runtime_paths"]["input"])
        self.assertEqual(2, len(value["failed_predecessors"]))
        self.assertTrue(all(not row["reusable"]
                            for row in value["failed_predecessors"]))
        self.assertFalse(value["effect_authorized"])

    def test_retained_packet_is_exact(self):
        source.validate_retained_packet()


if __name__ == "__main__":
    unittest.main()
