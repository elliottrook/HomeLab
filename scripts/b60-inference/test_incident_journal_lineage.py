import importlib.util,json,unittest
from pathlib import Path
p=Path(__file__).parent/'model-trial-20261106-r3/news_xpu_boundary.py'
spec=importlib.util.spec_from_file_location('incident_lineage_test',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Lineage(unittest.TestCase):
 def rows(self):
  return [{'__REALTIME_TIMESTAMP':str(t),'MESSAGE':v} for t,v in [(1794002063552040,'xe GPU reset'),(1794002063556039,'xe context\nfault detail'),(1794002063556348,'xe GPU fault')]]
 def check(self,rows):return m.verify_incident_journal('\n'.join(json.dumps(v) for v in rows),{1794002063552040,1794002063556039,1794002063556348})
 def test_context_presence_separate_from_hazard_count(self):self.assertEqual(self.check(self.rows()),2)
 def test_missing_context_refused(self):
  with self.assertRaises(AssertionError):self.check(self.rows()[::2])
 def test_duplicate_context_refused(self):
  with self.assertRaises(AssertionError):self.check(self.rows()+[self.rows()[1]])
 def test_new_fault_refused(self):
  with self.assertRaises(AssertionError):self.check(self.rows()+[{'__REALTIME_TIMESTAMP':'1794010000000000','MESSAGE':'xe GPU reset'}])
 def test_changed_context_profile_refused(self):
  r=self.rows();r[1]['MESSAGE']='xe GPU fault'
  with self.assertRaises(AssertionError):self.check(r)
if __name__=='__main__':unittest.main()
