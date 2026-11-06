import shutil,tempfile,unittest
from pathlib import Path
from benchmark_contract_preparation import inspect_contract,ROOT
class FrozenContractBridgeTests(unittest.TestCase):
 def fixture(self):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)/'peer';shutil.copytree(ROOT,p);return p
 def test_frozen_peer_format_never_supplies_missing_live_evidence_or_authority(self):
  r=inspect_contract()
  self.assertTrue(r['owner_frozen_contract_verified'])
  self.assertEqual(r['authority'],'not-granted')
  for k in ('ready_for_live_execution','milestone_accepted','case_contents_read','baseline_measurements_read','recovery_qualification_inferred_from_document'):self.assertIs(r[k],False)
 def test_nominal_run_is_not_per_class_p95_or_a_new_budget(self):
  r=inspect_contract();self.assertEqual(r['nominal_two_role_case_captures'],48)
  self.assertEqual(r['owner_model_calls_max_unchanged'],48)
  p=r['acceptance_sampling_requirements']['family_as_latency_class_projection']
  self.assertIs(p['accepted'],False);self.assertIs(p['model_call_budget_derived'],False)
  self.assertEqual(p['two_role_complete_answer_observations_min'],1200)
 def test_valid_shaped_changed_model_contract_is_still_refused(self):
  p=self.fixture();f=p/'contract.json';f.write_bytes(f.read_bytes().replace(b'reasoning-on-27b-plus',b'reasoning-off'))
  with self.assertRaisesRegex(ValueError,'owner freeze'):inspect_contract(p)
 def test_drifted_validator_is_rejected_before_any_of_its_code_executes(self):
  p=self.fixture();marker=p/'side-effect';(p/'full_aster_benchmark_contract_v1.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').touch()\n')
  with self.assertRaisesRegex(ValueError,'validator source'):inspect_contract(p)
  self.assertFalse(marker.exists())
