import ast,importlib.util,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
H=Path(__file__).parent/'entry-rescue-qualification-20261106-r6'
class RegisteredRoute(unittest.TestCase):
 def test_real_generated_run_chooses_matching_bridge(self):
  sp=importlib.util.spec_from_file_location('r6_actual_builder',H/'build_registration.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);b.build()
  tree=ast.parse((b.DEST/'lab_hours_reserved_runner.py').read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run');run.returns=None
  for name,bridge in [('b60-entry-backend-preservation-qualification-v1','b60_entry_rescue_card_bridge'),('b60-qwen36-35b-failure-capture-v1','b60_exclusive_card_bridge')]:
   calls=[];modules={}
   for module in ('b60_entry_rescue_card_bridge','b60_exclusive_card_bridge'):
    m=types.ModuleType(module);m.dispatch=lambda row,spec,m=module:calls.append(m) or 0;modules[module]=m
   w=types.ModuleType('lab_hours_workloads');w.validate_registry=lambda:None;w.validate_inactive_target=lambda *a,**k:None;modules[w.__name__]=w
   class Store:
    def __init__(self,*a):pass
    def get(self,*a):return {'workload':name}
   scope={'os':types.SimpleNamespace(geteuid=lambda:0),'ReservationStore':Store,'RESERVATIONS':None,'PILOT':None,'load_manifest':lambda:None,'workload':lambda n:object(),'RunError':RuntimeError,'json':__import__('json')}
   with patch.dict(sys.modules,modules):
    exec(compile(ast.fix_missing_locations(ast.Module(body=[run],type_ignores=[])),'actual_generated_run','exec'),scope);self.assertEqual(scope['run']('b60-test'),0)
   self.assertEqual(calls,[bridge])
if __name__=='__main__':unittest.main()
