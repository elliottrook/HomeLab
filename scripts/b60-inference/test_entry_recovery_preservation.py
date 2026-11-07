import importlib.util,unittest
from pathlib import Path
from types import SimpleNamespace
p=Path(__file__).parent/'entry-rescue-qualification-20261106-r6/entry_recovery.py';sp=importlib.util.spec_from_file_location('entry_recovery_under_test',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class Clock:
 def __init__(self):self.now=0
 def __call__(self):return self.now
 def sleep(self,n):self.now+=n
class Preservation(unittest.TestCase):
 def test_strict_wait_passes_actual_bound(self):
  c=Clock();calls=[]
  def verify(rows,deadline):calls.append(deadline);return len(calls)==3
  self.assertTrue(m.bounded_verify(verify,[],500,clock=c,sleep=c.sleep));self.assertEqual(calls,[45,45,45]);self.assertEqual(c.now,4)
 def test_unknown_state_never_becomes_pass(self):
  c=Clock();self.assertFalse(m.bounded_verify(lambda r,d:False,[],10,clock=c,sleep=c.sleep));self.assertLessEqual(c.now,10)
 def test_query_exception_is_not_masked(self):
  def bad(*a):raise ValueError('fake observation failed')
  with self.assertRaises(ValueError):m.bounded_verify(bad,[],10,clock=Clock())
 def fake(self,active=True,holder=True,guest=True,health=True,pid_change=False):
  events=[];writes={};root=SimpleNamespace(__truediv__=None)
  class Root:
   def __truediv__(self,n):return SimpleNamespace(exists=lambda:True)
  store=SimpleNamespace(root=Root(),write=lambda n,v,**kw:writes.setdefault(n,v))
  class Units:
   def verify(self,r,d):return True
   def observe(self,*a):return {'ActiveState':'active' if active else 'failed','UnitFileState':'enabled','MainPID':str(8 if pid_change and events else 7)}
   def isolate(self,rows,d):events.extend(('isolate',r['unit']) for r in rows);return True
  units=Units();adapter=SimpleNamespace(units=units,private={'units':[{'guest':'110','unit':'aster-llama.service','active':'active','enablement':'enabled'},{'guest':'104','unit':'aster-agent.service','active':'active','enablement':'enabled'}]},bookings=SimpleNamespace(get=lambda b:{'start_epoch':0}),_load=lambda:None,_guest=lambda *a:{'verified':guest})
  def call(*a):
   if not health:raise RuntimeError('health failed')
   return 'ExecMainStartTimestampMonotonic=12345\n'
  adapter._call=call
  def runner(cmd,t):events.append(('command',tuple(cmd)));return 0,'LoadState=not-found\nActiveState=inactive\nMainPID=0\nTasksCurrent=0\n'
  adapter.runner=runner;adapter.fence_experiments=lambda s:False
  m.install(adapter,store,kernel_check=lambda *a:{'new_kernel_hazard_count':0},gpu_users=lambda:{SimpleNamespace()} if False else ([SimpleNamespace(cgroup='/lxc/110/ns/system.slice/aster-llama.service')] if holder else []),clock=lambda:1)
  return adapter,events,writes
 def test_preserves_backend_and_fences_other_consumers(self):
  a,events,writes=self.fake();self.assertTrue(a.fence_experiments({'booking_id':'b60-test','entry_sha256':'a'*64,'restore_deadline':100}));self.assertIn(('isolate','aster-agent.service'),events);self.assertNotIn(('isolate','aster-llama.service'),events);self.assertIn('entry-backend-preservation-proof.json',writes)
 def test_failed_prior_start_refuses_without_backend_stop(self):
  a,events,writes=self.fake(active=False)
  with self.assertRaises(RuntimeError):a.fence_experiments({'booking_id':'b60-test','entry_sha256':'a'*64,'restore_deadline':100})
  self.assertFalse(any(v[0]=='isolate' for v in events))
 def test_unverified_artifact_refuses(self):
  a,events,writes=self.fake(guest=False)
  with self.assertRaises(RuntimeError):a.fence_experiments({'booking_id':'b60-test','entry_sha256':'a'*64,'restore_deadline':100})
  self.assertFalse(any(v[0]=='isolate' for v in events))
 def test_extra_or_missing_holder_refuses(self):
  a,events,writes=self.fake(holder=False)
  with self.assertRaises(RuntimeError):a.fence_experiments({'booking_id':'b60-test','entry_sha256':'a'*64,'restore_deadline':100})
  self.assertFalse(any(v[0]=='isolate' for v in events))
if __name__=='__main__':unittest.main()
