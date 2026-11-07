import ast,types,unittest
from pathlib import Path
P=Path(__file__).parent/'entry-rescue-qualification-20261106-r7/qualification.py'
class Exit86(BaseException):pass
class FaultPoint(unittest.TestCase):
 def setup_runner(self,*,prior=False,active=True,owner=True,verified=True,start_ok=True):
  records={'session.json':{'phase':'restoring','trial_failed':False}}
  if prior:records['entry-backend-start-intent.json']={'maximum_start_attempts':1}
  calls=[]
  class Root:
   def __truediv__(self,n):return types.SimpleNamespace(name=n,exists=lambda:n in records)
  class Store:
   root=Root()
   def write(self,n,v,**kw):
    if kw.get('immutable') and n in records:raise ValueError('fake duplicate proof')
    records[n]=v
   def read(self,n):return dict(records[n])
  def original(command,timeout):
   calls.append(tuple(command))
   if command==('pct','exec','110','--','systemctl','start','aster-llama.service'):return (0 if start_ok else 1),''
   if 'is-active' in command:return (0 if active else 3),'active' if active else 'inactive'
   return 0,''
  def require(v,c):
   if v is not True:raise RuntimeError(c)
  def exit_(code):self.assertEqual(code,86);raise Exit86()
  scope={'store':Store(),'b':'b60-test','m':{},'HERE':Path('/fixed'),'original':original,'require':require,'time':types.SimpleNamespace(time=lambda:1,sleep=lambda n:None),'bookings':types.SimpleNamespace(get=lambda b:{'end_epoch':2000}),'row':{'start_epoch':0},'kernel':lambda *a:None,'a':types.SimpleNamespace(_guest=lambda *a:{'verified':verified}),'scopes':types.SimpleNamespace(_show=lambda:{'MainPID':'123' if owner else '456'}),'os':types.SimpleNamespace(getpid=lambda:123,_exit=exit_)}
  tree=ast.parse(P.read_text());fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='runner');exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'real_r7_runner','exec'),scope)
  return scope['runner'],records,calls
 def test_fault_occurs_only_after_first_success_and_active_binding(self):
  run,records,calls=self.setup_runner()
  with self.assertRaises(Exit86):run(('pct','exec','110','--','systemctl','start','aster-llama.service'),30)
  self.assertTrue(records['qualification-owner-loss-intent.json']['after_first_accepted_start_and_health']);self.assertTrue(records['session.json']['trial_failed']);self.assertEqual(len([c for c in calls if 'start' in c]),1)
 def test_failed_first_start_never_fabricates_fault_point(self):
  run,records,calls=self.setup_runner(start_ok=False)
  with self.assertRaises(RuntimeError):run(('pct','exec','110','--','systemctl','start','aster-llama.service'),30)
  self.assertNotIn('qualification-owner-loss-intent.json',records)
 def test_failed_active_binding_never_fabricates_fault_point(self):
  run,records,calls=self.setup_runner(verified=False)
  with self.assertRaises(RuntimeError):run(('pct','exec','110','--','systemctl','start','aster-llama.service'),30)
  self.assertNotIn('qualification-owner-loss-intent.json',records)
 def test_guardian_does_not_inject_a_second_fault(self):
  run,records,calls=self.setup_runner(owner=False);self.assertEqual(run(('pct','exec','110','--','systemctl','start','aster-llama.service'),30),(0,''));self.assertNotIn('qualification-owner-loss-intent.json',records)
 def test_prior_active_start_is_idempotent_without_start_effect(self):
  run,records,calls=self.setup_runner(prior=True);self.assertEqual(run(('pct','exec','110','--','systemctl','start','aster-llama.service'),30),(0,''));self.assertFalse(any('start' in c for c in calls));self.assertFalse(records['entry-backend-idempotent-start.json']['new_backend_start_invoked'])
 def test_uncertain_prior_start_is_not_retried(self):
  run,records,calls=self.setup_runner(prior=True,active=False)
  with self.assertRaises(RuntimeError):run(('pct','exec','110','--','systemctl','start','aster-llama.service'),30)
  self.assertFalse(any('start' in c for c in calls));self.assertNotIn('entry-backend-idempotent-start.json',records)
if __name__=='__main__':unittest.main()
