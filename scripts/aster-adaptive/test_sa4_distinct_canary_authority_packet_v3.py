import unittest

import sa4_distinct_canary_authority_packet_v3 as source
import sa4_single_file_repair_contract_v1 as contract


class Tests(unittest.TestCase):
    def test_fresh_third_packet_is_unsigned(self):
        packet = source.build_unsigned(3000)
        grant = contract.decode_unique_json(packet["grant"])
        self.assertEqual(source.GRANT_ID, grant["grant_id"])
        self.assertNotIn(b"signature_hex", packet["approval_statement"])
        self.assertNotIn(b"signature_hex", packet["grant_statement"])

    def test_predecessor_grants_are_not_reused(self):
        self.assertNotIn(source.GRANT_ID, {
            "sa4-canary-v2-first-grant-v1-20261106",
            "sa4-canary-v2-second-grant-v1-20261106"})


if __name__ == "__main__":
    unittest.main()
