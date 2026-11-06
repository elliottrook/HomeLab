import unittest

import sa4_distinct_canary_authority_packet_v2 as source
import sa4_distinct_canary_plan_v1 as plan_source
import sa4_single_file_repair_contract_v1 as contract


class Tests(unittest.TestCase):
    def test_fresh_packet_is_unsigned_and_bound(self):
        packet = source.build_unsigned(2000)
        self.assertEqual({"plan", "approval", "approval_statement", "grant",
                          "grant_statement"}, set(packet))
        grant = contract.decode_unique_json(packet["grant"])
        self.assertEqual(source.GRANT_ID, grant["grant_id"])
        self.assertEqual(plan_source.PLAN_SHA256, grant["plan_sha256"])
        self.assertEqual(1, grant["max_uses"])
        self.assertNotIn(b"signature_hex", packet["approval_statement"])
        self.assertNotIn(b"signature_hex", packet["grant_statement"])

    def test_failed_grant_identity_is_not_reused(self):
        self.assertNotEqual("sa4-canary-v2-first-grant-v1-20261106",
                            source.GRANT_ID)


if __name__ == "__main__":
    unittest.main()
