import copy,tempfile,unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from fixed_candidate_command import compile_candidate
class CandidateCommandBoundaryTests(unittest.TestCase):
 def setUp(self):
  self.now=int(datetime(2026,11,6,3,10,tzinfo=ZoneInfo('America/Vancouver')).timestamp())
  self.booking=dict(booking_id='b60-exclusive-20261106',owner='b60-stream-a',kind='exclusive-stack',state='claimed',start_epoch=self.now,end_epoch=self.now+2700)
 def compile(self,b=None,**changes):return compile_candidate(b or self.booking,now_epoch=changes.get('now',self.now),trial_deadline_epoch=changes.get('deadline',self.now+1800))
 def test_candidate_is_in_exact_scope_the_qualified_fence_owns(self):
  v=self.compile();u='b60-exclusive-trial-b60-exclusive-20261106.service'
  self.assertEqual(v['owned_unit'],u);self.assertIn('--unit='+u,v['start_command']);self.assertEqual(v['stop_command'][-1],u)
  self.assertNotIn('--unit=aster-full-screen-qwen36.service',v['start_command'])
  self.assertIn('--property=KillMode=control-group',v['start_command']);self.assertIn('--property=RuntimeMaxSec=1800',v['start_command'])
 def test_exact_reasoning_runtime_and_zero_retry_survive_scope_adaptation(self):
  v=self.compile();c=v['start_command'];self.assertEqual(c[c.index('--reasoning')+1],'on')
  self.assertEqual(c[c.index('-c')+1],'8192');self.assertEqual(c[c.index('-np')+1],'1');self.assertNotIn('--draft-model',c)
  self.assertEqual(v['requests'],2);self.assertEqual(v['retries'],0);self.assertIs(v['ready_for_live_execution'],False);self.assertIs(v['live_admission_verified'],False)
 def test_unclaimed_foreign_or_injected_identity_cannot_compile(self):
  for k,x in [('state','reserved'),('owner','another-owner'),('kind','workload'),('booking_id','b60-exclusive-20261106;id'),('booking_id','b60-exclusive-20261105')]:
   b=dict(self.booking,**{k:x})
   with self.assertRaises(ValueError):self.compile(b)
 def test_stale_long_boolean_or_reserve_consuming_budget_is_refused(self):
  for changes in [dict(now=self.now-1),dict(deadline=self.now),dict(deadline=self.now+1801),dict(now=True)]:
   with self.assertRaises(ValueError):self.compile(**changes)
  b=dict(self.booking,end_epoch=self.now+2699)
  with self.assertRaises(ValueError):self.compile(b)
 def test_modified_command_source_never_executes(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'source.py';marker=Path(tmp)/'effect';p.write_text('from pathlib import Path\nPath('+repr(str(marker))+').touch()\n')
   with self.assertRaisesRegex(ValueError,'source drift'):compile_candidate(self.booking,now_epoch=self.now,trial_deadline_epoch=self.now+1800,source_path=p)
   self.assertFalse(marker.exists())
