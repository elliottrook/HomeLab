"""Actual retained public proof fixture, not fabricated qualification evidence."""
import ast,copy,hashlib,importlib.util,json,unittest
from pathlib import Path
R=Path(__file__).parents[2]
P=Path(__file__).parent/'entry-rescue-qualification-20261106-r7/b60_entry_rescue_card_bridge.py'
class Closure(unittest.TestCase):
 def setUp(self):
  sp=importlib.util.spec_from_file_location('r7_incident_gate_test',P);self.m=importlib.util.module_from_spec(sp);sp.loader.exec_module(self.m)
  self.actual=json.loads((R/'docs/projects/B60-Inference-Engineering/evidence/20261106-model-r3/r5-durable-closure.json').read_text())
 def test_actual_retained_postcheck_fixture_passes_exact_validator(self):
  self.assertTrue(self.m.validate_incident_closure(self.actual['closure'],self.actual['postcheck']))
 def test_actual_fixture_cannot_be_relabelled_as_assisted_pass(self):
  post=copy.deepcopy(self.actual['postcheck']);post['manual_assistance_required']=True
  with self.assertRaises(RuntimeError):self.m.validate_incident_closure(self.actual['closure'],post)
 def test_full_incident_verifier_and_validator_match_accepted_source(self):
  old=ast.parse((P.parent.parent/'model-trial-20261106-r3/b60_exclusive_card_bridge.py').read_text());new=ast.parse(P.read_text())
  for name in ('validate_incident_closure','require_incident_closed'):
   a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name);b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name);self.assertEqual(ast.dump(a),ast.dump(b))
if __name__=='__main__':unittest.main()
