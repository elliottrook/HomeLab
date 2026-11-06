import unittest
from unittest import mock
import sa4_distinct_canary_plan_v2 as old_plan
import sa4_distinct_canary_plan_v3 as plan
import sa4_fixed_transaction_runner_v8 as old_runner
import sa4_fixed_transaction_runner_v9 as runner
import sa4_single_file_repair_contract_v1 as contract

class V9Tests(unittest.TestCase):
    def test_only_plan_identity_changes(self):
        old=contract.decode_unique_json(old_plan.build_plan()); new=contract.decode_unique_json(plan.build_plan())
        self.assertEqual(plan.PLAN_ID,new.pop("plan_id")); old.pop("plan_id"); self.assertEqual(old,new)
    def test_runner_scopes_fresh_paths(self):
        original=(old_runner.INPUT_DIR,old_runner.EVIDENCE_DIR,old_runner.LEDGER_ROOT,old_runner.OPERATION_ID)
        with mock.patch.object(old_runner,"execute",return_value={"ok":True}): self.assertEqual({"ok":True},runner.execute(9))
        self.assertEqual(runner.EXPECTED_PREDECESSOR,original)
        self.assertEqual(original,(old_runner.INPUT_DIR,old_runner.EVIDENCE_DIR,old_runner.LEDGER_ROOT,old_runner.OPERATION_ID))
    def test_rejects_arguments(self):
        with self.assertRaises(ValueError): runner.main(["x"])

if __name__ == "__main__": unittest.main()
