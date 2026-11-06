import importlib.util,json,unittest
from pathlib import Path
D=Path(__file__).parent/'post-xe-qualification-20261106'
def load(n):
 s=importlib.util.spec_from_file_location('post_xe_'+n,D/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class QualificationTests(unittest.TestCase):
 def test_fixed_predicates_and_reject_incomplete_or_false(self):
  m=load('known_answer_requests')
  for i,want in enumerate(m.EXPECTED):
   content=want if i==0 else json.dumps(want)
   value={'model':m.MODEL,'choices':[{'finish_reason':'stop','message':{'content':content}}]}
   self.assertTrue(m.verify_response(i,200,json.dumps(value).encode())['predicate_passed'])
   value['choices'][0]['finish_reason']='length'
   self.assertFalse(m.verify_response(i,200,json.dumps(value).encode())['predicate_passed'])
  self.assertFalse(m.verify_response(0,200,b'{"choices":[{}]}')['predicate_passed'])
  self.assertEqual(json.loads(m.payload(0))['chat_template_kwargs'],{'enable_thinking':False})
 def test_failures_retained_stop_after_first_no_retries(self):
  m=load('known_answer_requests')
  class O:
   calls=0
   def open(self,*a,**kw):self.calls+=1;raise TimeoutError('PRIVATE')
  o=O();v=m.run(read_key=lambda:'not-a-real-key-value',opener=o)
  self.assertEqual(o.calls,1);self.assertEqual(v['state'],'failed');self.assertNotIn('PRIVATE',json.dumps(v));self.assertEqual(v['attempted_requests'],1)
  host=load('qualification');self.assertEqual(host.validate_packet(v),v)
  v['raw_secret']='forbidden'
  with self.assertRaises(RuntimeError):host.validate_packet(v)
 def test_runtime_command_is_bounded_by_controller_and_no_reset(self):
  m=load('fixed_command');cmd=m.start_command();self.assertIn('--reasoning',cmd);self.assertIn(m.MODEL,cmd);self.assertNotIn('reboot',cmd)
  source=(D/'qualification.py').read_text()
  self.assertIn("result.get('outcome')=='complete-restored'",source)
  self.assertIn('adapter.units.runner=runner',source)
  self.assertIn("store.write(p.name,{'booking_id':b",source)
  self.assertIn("--property=RuntimeMaxSec=300",source)
  self.assertNotIn('session.recover(',source)
 def test_registration_preserves_peer_and_snapshot(self):
  m=load('build_registration');m.build()
  s=importlib.util.spec_from_file_location('post_xe_registry',m.DEST/'lab_hours_workloads.py');w=importlib.util.module_from_spec(s);__import__('sys').modules[s.name]=w;s.loader.exec_module(w)
  self.assertIn(m.WORKLOAD,w.REGISTERED_WORKLOADS)
  self.assertIn('aster-news-video-musetalk-openvino-smoke-v1',w.WORKLOADS)
  self.assertEqual(w.WORKLOADS[m.WORKLOAD].request_count,3)
if __name__=='__main__':unittest.main()
