import unittest

import sa4_distinct_canary_authority_packet_v1 as source
import sa4_distinct_canary_plan_v1 as plan_source
import sa4_single_file_repair_contract_v1 as contract


class Tests(unittest.TestCase):
    def test_fresh_exact_grant(self):
        packet = source.build_unsigned(1000)
        grant = contract.decode_unique_json(packet["grant"])
        approval = contract.decode_unique_json(packet["approval"])
        self.assertEqual(source.GRANT_ID, grant["grant_id"])
        self.assertEqual(plan_source.PLAN_SHA256, grant["plan_sha256"])
        self.assertEqual(plan_source.BEFORE_SHA256, grant["target_sha256"])
        self.assertEqual(1, grant["max_uses"])
        self.assertEqual(1900, grant["expires_epoch"])
        self.assertEqual(2800, approval["expires_epoch"])

    def test_statements_are_unsigned_no_effect_inputs(self):
        packet = source.build_unsigned(1000)
        for name in ("approval_statement", "grant_statement"):
            value = contract.decode_unique_json(packet[name])
            self.assertNotIn("signature_hex", value)
            self.assertEqual("signature-only-no-effect", value["authority"])

    def test_bad_time_rejected(self):
        for value in (0, -1, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                source.build_unsigned(value)


if __name__ == "__main__":
    unittest.main()
