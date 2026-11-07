import importlib.util,unittest
from pathlib import Path
P=Path(__file__).parent/'model-trial-20261106-r8/model_trial.py'
class Codes(unittest.TestCase):
 def setUp(self):
  sp=importlib.util.spec_from_file_location('r8_failure_code_test',P);self.m=importlib.util.module_from_spec(sp);sp.loader.exec_module(self.m)
 def test_known_restoration_code_is_retained_even_from_session_error(self):
  class SessionError(Exception):pass
  self.assertEqual(self.m.failure_code(SessionError('RESTORATION_NOT_VERIFIED')),'RESTORATION_NOT_VERIFIED')
 def test_untrusted_error_text_never_becomes_exported_code(self):
  for value in ('private/path/key=secret','SENSITIVEUNKNOWNVALUE','MODEL_REQUEST_FAILED plus untrusted text'):
   self.assertEqual(self.m.failure_code(RuntimeError(value)),'UNCLASSIFIED')
if __name__=='__main__':unittest.main()
