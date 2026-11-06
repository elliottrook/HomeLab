import unittest
from unittest import mock
import sa4_fixed_transaction_runner_v10 as source, sa4_fixed_transaction_runner_v9 as previous, sa4_fixed_transaction_runner_v3 as core, sa4_target_registry_v2 as r2, sa4_target_registry_v3 as r3
class Tests(unittest.TestCase):
 def test_binding_scoped(self):
  original=(previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID,core.registry)
  seen=[]
  def invoked(now): seen.append(core.registry); return {"ok":now}
  with mock.patch.object(previous,"execute",side_effect=invoked):
   self.assertEqual({"ok":1},source.execute(1))
  self.assertEqual([r3],seen)
  self.assertEqual(original,(previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID,core.registry))
 def test_registry_expectations(self): self.assertIs(core.registry,r2); self.assertIsNot(r2,r3)
 def test_args(self):
  with self.assertRaises(ValueError): source.main(["x"])
if __name__=="__main__": unittest.main()
