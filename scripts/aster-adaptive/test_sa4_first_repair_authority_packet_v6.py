import unittest
import sa4_first_repair_authority_packet_v6 as source
import sa4_single_file_repair_contract_v1 as contract
class Tests(unittest.TestCase):
    def test_unique_exact_grant(self):
        value=contract.decode_unique_json(source.build_unsigned(1000)["grant"]); self.assertEqual(source.GRANT_ID,value["grant_id"]); self.assertNotIn("v5",value["grant_id"]); self.assertEqual(1,value["max_uses"])
    def test_deadlines(self):
        packet=source.build_unsigned(1000); self.assertEqual(1900,contract.decode_unique_json(packet["grant"])["expires_epoch"]); self.assertEqual(2800,contract.decode_unique_json(packet["approval"])["expires_epoch"])
    def test_bad_time(self):
        for value in (0,-1,1.5):
            with self.assertRaises(ValueError): source.build_unsigned(value)
if __name__=="__main__": unittest.main()
