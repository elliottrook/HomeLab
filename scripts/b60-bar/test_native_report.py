import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('native_report',Path(__file__).with_name('summarize-native-openvino.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class ReportTests(unittest.TestCase):
 def make(self,root,different_length=False,different_prompt=False):
  for fixture,target in zip(s.FIXTURES,[76,2060,8012]):
   for phase in ['sycl-pre','native-openvino','sycl-post']:
    native=phase=='native-openvino';tokens=127 if native and different_length and fixture!='b60-tg128-cold' else 128
    samples=[]
    for i in range(6):
     role='warmup' if i==0 else 'measured'
     samples.extend([{'phase':'prefill','control_role':role,'correct':True,'tokens':target}, {'phase':'decode','control_role':role,'correct':True,'tokens':tokens,'seconds':2 if native else 3,'tokens_per_second':60}])
    d={'fixture':fixture,'health_passed':True,'prompt_sha256':'other' if native and different_prompt else 'same','samples':samples}
    d['generation_policy']={'ignore_eos':fixture=='b60-tg128-cold','max_output_tokens':128}
    (root/f'run-{phase}-{fixture}.json').write_text(json.dumps(d))
 def test_incomplete_never_becomes_a_speed_result(self):
  with tempfile.TemporaryDirectory() as d:self.assertFalse(s.summarize(Path(d),'run')['complete'])
 def test_matched_latency_requires_same_input_and_output(self):
  for length,prompt in [(False,False),(True,False),(False,True)]:
   with tempfile.TemporaryDirectory() as d:
    root=Path(d);self.make(root,length,prompt);r=s.summarize(root,'run')
    self.assertTrue(r['complete'])
    for fixture,v in r['fixtures'].items():
     self.assertEqual(v['matched_latency_claim_supported'],(not length or fixture=='b60-tg128-cold') and not prompt)
     self.assertNotIn('server_decode_improvement_percent',v)
 def test_fixed_length_policy_must_be_identical(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.make(root)
   p=root/'run-native-openvino-b60-tg128-cold.json';data=json.loads(p.read_text());data['generation_policy']['ignore_eos']=False;p.write_text(json.dumps(data))
   with self.assertRaises(AssertionError):s.summarize(root,'run')
if __name__=='__main__':unittest.main()
