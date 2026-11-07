"""Exercise actual fixed capsule argv guards with no files or services."""
import importlib.util,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).parent
class GatewayScopeTests(unittest.TestCase):
 def load(self,folder):
  spec=importlib.util.spec_from_file_location('fixed_gateway_scope_fixture',D/folder/'guest_entry_scope.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 def run_case(self,m,args):
  old=frozenset({'/etc/aster-llama.env'});seen=[]
  def endpoint():seen.append(list(sys.argv));return 0
  gc=types.SimpleNamespace(EXACT_CONFIG_FILES=old|{'/etc/epub-narration/gateway.env'},main=endpoint)
  prep=types.SimpleNamespace(EXACT_CONFIG_FILES=gc.EXACT_CONFIG_FILES,main=endpoint)
  with patch.object(m,'initialize',return_value=(gc,prep,old)),patch.object(sys,'argv',['fixed',*args]):
   try:result=m.main()
   finally:self.assertEqual(gc.EXACT_CONFIG_FILES,old);self.assertEqual(prep.EXACT_CONFIG_FILES,old)
  return result,seen
 def test_prepare_only_own_booking_guest(self):
  for folder in ('post-xe-qualification-20261106-r5','model-trial-20261106-r3'):
   m=self.load(folder);result,seen=self.run_case(m,['prepare','--guest-id','116','--booking-id',m.BOOKING]);self.assertEqual(result,0);self.assertEqual(len(seen),1)
   with self.assertRaises(RuntimeError):self.run_case(m,['prepare','--guest-id','110','--booking-id',m.BOOKING])
   with self.assertRaises(RuntimeError):self.run_case(m,['prepare','--guest-id','116','--booking-id','b60-exclusive-20261106-day-r99'])
 def test_checkpoint_refuses_path_escape_and_missing_effect_authority(self):
  m=self.load('model-trial-20261106-r3');root='/var/lib/local-ai-lab-entry/'+m.BOOKING
  args=['checkpoint','capture','--guest-id','116','--plan',root+'/plan.json','--checkpoint',root+'/files','--receipt',root+'/receipt.json','--deadline','1794016500','--effect-authorized']
  self.assertEqual(self.run_case(m,args)[0],0)
  with self.assertRaises(RuntimeError):self.run_case(m,args[:-1])
  bad=list(args);bad[5]='/etc/other.env'
  with self.assertRaises(RuntimeError):self.run_case(m,bad)
  with self.assertRaises(RuntimeError):self.run_case(m,args+['--unexpected'])
 def test_model_scope_matches_live_qualified_scope_except_booking(self):
  source=(D/'post-xe-qualification-20261106-r5/guest_entry_scope.py').read_text().replace('b60-exclusive-20261106-day-r5','b60-exclusive-20261106-day-r4')
  self.assertEqual(source,(D/'model-trial-20261106-r3/guest_entry_scope.py').read_text())
if __name__=='__main__':unittest.main()
