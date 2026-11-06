import unittest
import sa4_registration_mismatch_reconciler_v2 as source
import sa4_single_file_repair_contract_v1 as contract
class Tests(unittest.TestCase):
 def test_nested_canonical(self):
  raw=contract.canonical({"a":{"b":1}}); self.assertEqual({"a":{"b":1}},source._json(raw))
 def test_duplicate_rejected(self):
  with self.assertRaises(ValueError): source._json(b'{"a":{"b":1,"b":2}}\n')
 def test_args(self):
  with self.assertRaises(ValueError): source.main(["x"])
if __name__=="__main__": unittest.main()
