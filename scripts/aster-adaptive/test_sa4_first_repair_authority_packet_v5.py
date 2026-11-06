import unittest
import sa4_first_repair_authority_packet_v5 as source
import sa4_first_repair_transaction_release_v5 as release
import sa4_single_file_repair_contract_v1 as contract
import sa4_authenticated_authority_v1 as authority

class Tests(unittest.TestCase):
    def test_exact_fresh_packet(self):
        packet=source.build_unsigned(1000); grant=contract.decode_unique_json(packet["grant"])
        self.assertEqual(source.GRANT_ID,grant["grant_id"]); self.assertEqual(release.PLAN_SHA256,authority.sha256(packet["plan"]))
        self.assertNotIn("v4",grant["grant_id"]); self.assertEqual(1,grant["max_uses"])
    def test_short_lived(self):
        packet=source.build_unsigned(1000)
        self.assertEqual(2800,contract.decode_unique_json(packet["approval"])["expires_epoch"])
        self.assertEqual(1900,contract.decode_unique_json(packet["grant"])["expires_epoch"])
    def test_bad_time(self):
        for value in (0,-1,1.5,"1"):
            with self.assertRaises(ValueError): source.build_unsigned(value)

if __name__=="__main__": unittest.main()
