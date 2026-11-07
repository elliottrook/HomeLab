"""Offline existing-route delta tests; no controller acceptance is fabricated."""
import ast,hashlib,importlib.util,json,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
D=Path(__file__).parent
class Update(unittest.TestCase):
 def setUp(self):
  p=D/'model-trial-20261106-r8/build_registration.py';sp=importlib.util.spec_from_file_location('r8_delta_under_test',p);self.m=importlib.util.module_from_spec(sp);sp.loader.exec_module(self.m)
  p=D/'entry-rescue-qualification-20261106-r7/build_registration.py';sp=importlib.util.spec_from_file_location('r7_fixture_builder',p);b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);b.build();self.root=b.DEST
 def test_existing_route_only_preserves_runner_and_all_unrelated_pins(self):
  raw={n:(self.root/n).read_bytes() for n in ('lab_hours_workloads.py','lab_hours_reserved_runner.py','lab_hours_release_manifest.json')};bridge=(D/'model-trial-20261106-r8/b60_exclusive_card_bridge.py').read_bytes();out=self.m.update(raw['lab_hours_workloads.py'],raw['lab_hours_reserved_runner.py'],raw['lab_hours_release_manifest.json'],bridge)
  self.assertEqual(out['lab_hours_reserved_runner.py'],raw['lab_hours_reserved_runner.py']);before=json.loads(raw['lab_hours_release_manifest.json'])['pins'];after=json.loads(out['lab_hours_release_manifest.json'])['pins'];self.assertEqual(set(before),set(after))
  self.assertEqual({k:v for k,v in before.items() if k not in ('lab_hours_workloads.py','b60_exclusive_card_bridge.py')},{k:v for k,v in after.items() if k not in ('lab_hours_workloads.py','b60_exclusive_card_bridge.py')})
  old=before['b60_exclusive_card_bridge.py'];new=hashlib.sha256(bridge).hexdigest();self.assertEqual(raw['lab_hours_workloads.py'].replace(old.encode(),new.encode()),out['lab_hours_workloads.py'])
 def test_builder_refuses_without_actual_acceptance(self):
  with tempfile.TemporaryDirectory() as d, patch.object(self.m,'HERE',Path(d)):
   with self.assertRaises(FileNotFoundError):self.m.build()
 def test_live_gate_refuses_unrecorded_acceptance_before_any_proof_read(self):
  p=D/'model-trial-20261106-r8/b60_exclusive_card_bridge.py';sp=importlib.util.spec_from_file_location('r8_pending_gate',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  with patch.object(m,'CONTROLLER_ACCEPTANCE_SHA256',None),patch.object(m,'protected',side_effect=AssertionError('proof read must not occur')):
   with self.assertRaisesRegex(RuntimeError,'ACTUAL_CONTROLLER_ACCEPTANCE_NOT_RECORDED'):m.require_controller_qualified()
if __name__=='__main__':unittest.main()
