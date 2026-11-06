import copy
from pathlib import Path
import unittest
import sa4_effect_controller_inactive_install_result_v1 as result
import sa4_single_file_repair_contract_v1 as contract

RAW=(Path(__file__).parents[2]/"docs/projects/AI Projects/evidence/SA4-effect-controller-inactive-install-result-2026-11-05.json").read_bytes()

class Tests(unittest.TestCase):
    def test_exact_result(self):
        value=result.validate(RAW)
        self.assertEqual(3,value["changes_validated"]); self.assertTrue(value["inactive"])
    def test_effect_mutations_fail_closed(self):
        original=contract.decode_unique_json(RAW)
        for key in ("controller_invoked","signer_invoked","authority_touched","target_touched"):
            value=copy.deepcopy(original); value[key]=True
            with self.subTest(key),self.assertRaises(ValueError): result.validate(contract.canonical(value))
    def test_row_drift_fails_closed(self):
        value=contract.decode_unique_json(RAW); value["changes"][0]["link_count"]=2
        with self.assertRaises(ValueError): result.validate(contract.canonical(value))

if __name__=="__main__": unittest.main()
