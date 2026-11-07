import importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).parent/'model-trial-20261106-r8/news_xpu_boundary.py'
sp=importlib.util.spec_from_file_location('structured_kernel_test',P);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class Structured(unittest.TestCase):
 def test_multiline_device_fault_is_not_hidden(self):
  for message in ('xe device context\nfault detail','xe device\nlost','out of\nmemory'):
   self.assertEqual(m.message_hazard(message),1)
  with self.assertRaises(AssertionError):m.verify_clean_kernel(json.dumps({'MESSAGE':'xe device context\nfault detail'}))
 def test_separate_unrelated_messages_do_not_form_false_device_fault(self):
  raw='\n'.join(json.dumps({'MESSAGE':v}) for v in ('xe frequency changed','unrelated storage error'))
  self.assertTrue(m.verify_clean_kernel(raw))
 def test_unknown_message_shape_refuses(self):
  for value in (None,[120,101],{'text':'normal'}):
   with self.assertRaises(AssertionError):m.verify_clean_kernel(json.dumps({'MESSAGE':value}))
 def test_incident_missing_message_refuses(self):
  with self.assertRaises(AssertionError):m.verify_incident_journal(json.dumps({'__REALTIME_TIMESTAMP':'1794010000000000'}),{1794002063552040,1794002063556039,1794002063556348})
 def test_exact_three_original_complete_messages_are_bound(self):
  pairs=[(1794002063552040,'xe GPU reset'),(1794002063556039,'xe context\nfault detail'),(1794002063556348,'xe GPU fault')];raw='\n'.join(json.dumps({'__REALTIME_TIMESTAMP':str(t),'MESSAGE':v}) for t,v in pairs)
  self.assertEqual(m.verify_incident_journal(raw,{t for t,v in pairs}),3)
  with self.assertRaises(AssertionError):m.verify_incident_journal(raw+'\n'+json.dumps({'__REALTIME_TIMESTAMP':'1794010000000000','MESSAGE':'xe context\nfault detail'}),{t for t,v in pairs})
if __name__=='__main__':unittest.main()
