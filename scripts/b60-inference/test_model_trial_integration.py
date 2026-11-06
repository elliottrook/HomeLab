"""Failure-path tests for the actual fixed production composition, no live effects."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).parent/'model-trial-20261106/model_trial.py'
spec=importlib.util.spec_from_file_location('fixed_model_trial_test',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Root:
 def __init__(self,store,name=''):self.store,self.name=store,name
 def __truediv__(self,name):return Root(self.store,name)
 def exists(self):return self.name in self.store.v
class Store:
 def __init__(self):
  self.root=Root(self);self.events=[]
  self.source={n:{'dev':1,'ino':i,'bytes':10,'uid':0,'gid':0,'mode':0o700 if n=='root' else 0o400} for n,i in [('root',2),('model',3)]}
  self.v={'model-intent.json':{'booking_id':'b60-test','entry_sha256':'a'*64,'model_sha256':m.MODEL_SHA},'session.json':{'booking_id':'b60-test','entry_sha256':'a'*64},'model-preflight.json':{'source':self.source,'target_entry':{'exists':False}}}
 def read(self,n):return copy.deepcopy(self.v[n])
 def write(self,n,v,**kw):self.events.append(v.get('phase'));self.v[n]=copy.deepcopy(v)
class Adapter:
 def __init__(self):self.calls=[]
 def _call(self,c,*a):self.calls.append(c);return ''

class IntegrationTests(unittest.TestCase):
 def setUp(self):self.store=Store();self.adapter=Adapter()
 def test_exact_mapping_required(self):
  good={'mounts':1,'dev':1,'ino':2,'readonly':True,'symlink':False}
  self.assertTrue(m.exact_target(good,{'dev':1,'ino':2}))
  for k,v in [('mounts',2),('dev',9),('ino',8),('readonly',False),('symlink',True)]:
   self.assertFalse(m.exact_target(dict(good,**{k:v}),{'dev':1,'ino':2}))
 def test_recovery_requires_no_production_mount_before_custody(self):
  absent={'mounts':0,'exists':False};events=[]
  with patch.object(m,'source_metadata',return_value=self.store.source),patch.object(m,'target_observation',return_value=absent),patch.object(m.os,'chown',side_effect=lambda *a,**kw:events.append('custody')):
   m.cleanup(self.adapter,self.store,100)
  self.assertEqual(events,['custody','custody']);self.assertEqual(self.store.events,['custody-intent','verified'])
 def test_foreign_mount_retained_without_chown(self):
  with patch.object(m,'source_metadata',return_value=self.store.source),patch.object(m,'target_observation',return_value={'mounts':1,'dev':99}),patch.object(m,'namespace_action') as unmount,patch.object(m.os,'chown') as chown:
   with self.assertRaises(RuntimeError):m.cleanup(self.adapter,self.store,100)
   unmount.assert_not_called();chown.assert_not_called()
 def test_crash_after_unmount_resumes_custody(self):
  self.store.v['model-namespace-intent.json']={'private_namespace':'mnt:[99999999]'}
  with patch.object(m,'source_metadata',return_value=self.store.source),patch.object(m,'target_observation',return_value={'mounts':0,'exists':False}),patch.object(m,'namespace_action') as unmount,patch.object(m.os,'chown'):
   m.cleanup(self.adapter,self.store,100);unmount.assert_not_called()
  self.assertEqual(self.store.events,['custody-intent','verified'])
 def test_changed_source_or_entry_refuses_cleanup(self):
  for drift in ('entry','inode','custody'):
   self.setUp();source=copy.deepcopy(self.store.source)
   if drift=='entry':self.store.v['session.json']['entry_sha256']='other'
   if drift=='inode':source['root']['ino']=123
   if drift=='custody':source['model']['uid']=42
   with patch.object(m,'source_metadata',return_value=source),patch.object(m.os,'chown') as chown:
    with self.assertRaises(RuntimeError):m.cleanup(self.adapter,self.store,100)
    chown.assert_not_called()
 def test_live_candidate_namespace_blocks_custody(self):
  self.store.v['model-namespace-intent.json']={'private_namespace':'mnt:[12]'}
  with patch.object(m,'source_metadata',return_value=self.store.source),patch.object(m,'Path') as path,patch.object(m.os,'readlink',return_value='mnt:[12]'),patch.object(m.os,'chown') as chown:
   path.return_value.glob.return_value=[Path('/fake/12')]
   with self.assertRaises(RuntimeError):m.cleanup(self.adapter,self.store,100)
   chown.assert_not_called()
 def test_incomplete_custody_blocks_verified_receipt(self):
  changed=copy.deepcopy(self.store.source);changed['model']['uid']=100999;changed['model']['gid']=100991
  with patch.object(m,'source_metadata',side_effect=[changed,changed]),patch.object(m,'target_observation',return_value={'mounts':0,'exists':False}),patch.object(m.os,'chown'):
   with self.assertRaises(RuntimeError):m.cleanup(self.adapter,self.store,100)
   self.assertNotIn('verified',self.store.events)
 def test_kernel_hazard_rejected(self):
  for text in ('xe 0000:04:00.0: GPU reset','Out of memory: killed process','xe device lost'):
   self.adapter._call=lambda *args:text
   with self.assertRaises(RuntimeError):m.kernel_check(self.adapter,100,0)
 def test_mount_parent_propagation_refused(self):
  sp=importlib.util.spec_from_file_location('namespace_fixed_test',P.parent/'namespace_mount.py');n=importlib.util.module_from_spec(sp);sp.loader.exec_module(n)
  private='1 0 8:1 / / rw master:1 - ext4 /dev/root rw'
  shared='1 0 8:1 / / rw shared:2 - ext4 /dev/root rw'
  self.assertTrue(n.private_target_parent(private,'/opt/models/aster-first-screen'))
  self.assertFalse(n.private_target_parent(shared,'/opt/models/aster-first-screen'))
  child='2 1 8:1 /opt /opt rw - ext4 /dev/root rw'
  self.assertTrue(n.private_target_parent(shared+'\n'+child,'/opt/models/aster-first-screen'))
  with self.assertRaises(n.MountError):n.private_target_parent('bad','/opt/models/aster-first-screen')
 def test_actual_guest_fdinfo_parser_matches_accepted_xe_counters(self):
  import ast,contextlib,io,json,types
  tree=ast.parse(P.read_text());trial=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='trial')
  code=next(ast.literal_eval(n.value) for n in ast.walk(trial) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
  class Fake:
   raw=''
   def __init__(self,*args):pass
   def __truediv__(self,other):return self
   def glob(self,other):return [self]
   def read_text(self):return self.raw
  for key,present in [('drm-resident-vram0',True),('wrong-counter',False)]:
   Fake.raw='drm-driver: xe\n'+key+': 20000000 KiB\ndrm-resident-gtt: 1024 KiB\n'
   output=io.StringIO()
   with patch.dict(sys.modules,{'pathlib':types.SimpleNamespace(Path=Fake)}),patch.object(sys,'argv',['probe','12']),contextlib.redirect_stdout(output):exec(code,{})
   value=json.loads(output.getvalue());self.assertEqual(value['vram_field_present'],present)
   self.assertTrue(value['gtt_field_present']);self.assertEqual(value['gtt_resident_kib'],1024)
   if present:self.assertEqual(value['vram_resident_kib'],20000000)
 def test_synthetic_request_budget_and_structure(self):
  sp=importlib.util.spec_from_file_location('guest_fixed_test',P.parent/'guest_requests.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
  import json
  self.assertEqual(len(g.PROMPTS),2);self.assertEqual(g.TIMEOUT,60)
  self.assertEqual(json.loads(g.payload(g.PROMPTS[0]))['max_tokens'],1024)
  with self.assertRaises(g.RequestError):g.payload('arbitrary')

if __name__=='__main__':unittest.main()
