import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('openvino-trial-server.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class NativeTests(unittest.TestCase):
 def test_ignore_eos_requires_explicit_bounded_throughput_mode(self):
  valid={'messages':[{'role':'user','content':'synthetic'}],'max_tokens':128,'ignore_eos':True}
  s.validate_payload(valid)
  for change in [{'ignore_eos':1},{'max_tokens':256},{'response_format':{'type':'json_schema','json_schema':{'schema':{}}}}]:
   with self.assertRaises(AssertionError):s.validate_payload({**valid,**change})
 def test_bounds_and_unsupported_features_fail_closed(self):
  valid={'messages':[{'role':'user','content':'synthetic'}],'max_tokens':128}
  self.assertEqual(s.validate_payload(valid)[1],128)
  for change in [{'max_tokens':257},{'max_tokens':True},{'stream':True},{'tools':[{}]},{'temperature':0.2},{'messages':[{'role':'user','content':[]}]}]:
   with self.assertRaises((AssertionError,ValueError)):s.validate_payload({**valid,**change})
 def test_native_metrics_are_not_fake_prefill_or_cache_measurements(self):
  class M:
   def get_num_generated_tokens(self):return 128
   def get_num_input_tokens(self):return 76
   def get_throughput(self):return SimpleNamespace(mean=55.0)
   def get_ttft(self):return SimpleNamespace(mean=120.0)
  r=s.metric_response(SimpleNamespace(perf_metrics=M(),texts=['synthetic']))
  self.assertEqual(r['usage']['completion_tokens'],128)
  self.assertEqual(r['timings']['predicted_per_second'],55.0)
  self.assertNotIn('prompt_ms',r['timings'])
  self.assertNotIn('prompt_tokens_cached',r['usage'])
  self.assertFalse(r['trial_metadata']['production_api_parity'])
if __name__=='__main__':unittest.main()
