"""Historical jobs retain exact chronology; current-task drift still refuses."""
import copy,importlib.util,os,sys,unittest
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
root=Path(__file__).parent/'model-trial-20261106-r2'
sp=importlib.util.spec_from_file_location('b60_history_test',root/'backup_chain_history.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
SOURCE=os.environ.get('B60_EXCLUSIVE_SOURCE_ROOT','/private/tmp/b60-resource-checkpoint-20261104/scripts/local-ai')
class Tests(unittest.TestCase):
 def setUp(self):
  sys.path.insert(0,SOURCE);self.addCleanup(lambda:sys.path.remove(SOURCE))
  self.epoch=lambda h,minute=0:int(datetime(2026,11,6,h,minute,tzinfo=ZoneInfo('America/Vancouver')).timestamp())
  self.now=self.epoch(11,30);jobs=[];tasks=[]
  for i,h in [(1,1),(3,2),(2,3)]:
   j={'id':i+10,'method':'rsynctask.run','arguments':[i],'state':'SUCCESS','time_started':{'$date':self.epoch(h)*1000},'time_finished':{'$date':(self.epoch(h)+60)*1000}}
   jobs.append(j);tasks.append({'id':i,'enabled':True,'schedule':{'hour':str(h),'minute':'0'},'job':copy.deepcopy(j)})
  tasks.sort(key=lambda r:r['id']);tasks[0]['job'].update(id=99,time_started={'$date':self.epoch(10,29)*1000},time_finished={'$date':(self.epoch(10,29)+40)*1000})
  self.v={'schema':'b60-truenas-chain-history.v1','source':'truenas@192.168.20.40','producer_sha256':m.CAPTURE_SHA,'observed_epoch':self.now,'tasks':tasks,'jobs':jobs+[copy.deepcopy(tasks[0]['job'])]};self.current=copy.deepcopy(tasks)
 def select(self):return m.select_history(self.v,self.current,cycle='2026_11_06',now=self.now,artifact_ctimes=[self.epoch(0,45)])
 def test_genuine_ordered_history_survives_redundant_late_success(self):
  chosen=self.select();self.assertEqual([r['job']['id'] for r in chosen],[11,13,12]);self.assertEqual(self.current[0]['job']['id'],99)
 def test_latest_job_change_or_active_state_refuses(self):
  for field,value in [('id',100),('state','RUNNING'),('state','FAILED')]:
   self.setUp();self.current[0]['job'][field]=value
   with self.assertRaises(RuntimeError):self.select()
 def test_missing_or_failed_historical_predecessor_refuses(self):
  for mode in ('missing','failed','wrong-task'):
   self.setUp()
   if mode=='missing':self.v['jobs']=[j for j in self.v['jobs'] if j['id']!=11]
   if mode=='failed':self.v['jobs'][0]['state']='FAILED'
   if mode=='wrong-task':self.v['jobs'][0]['arguments']=[42]
   with self.assertRaises(RuntimeError):self.select()
 def test_stale_future_source_and_wrong_producer_refuse(self):
  for field,value in [('observed_epoch',self.now-7201),('observed_epoch',self.now+1),('producer_sha256','x'*64)]:
   self.setUp();self.v[field]=value
   with self.assertRaises(RuntimeError):self.select()
 def test_newer_archives_and_wrong_cycle_refuse(self):
  with self.assertRaises(RuntimeError):m.select_history(self.v,self.current,cycle='2026_11_06',now=self.now,artifact_ctimes=[self.epoch(4)])
  with self.assertRaises(RuntimeError):m.select_history(self.v,self.current,cycle='2026_11_07',now=self.now,artifact_ctimes=[self.epoch(0,45)])
 def test_schedule_drift_refuses_even_when_capture_matches(self):
  self.v['tasks'][0]['schedule']['hour']='2';self.current=copy.deepcopy(self.v['tasks'])
  with self.assertRaises(RuntimeError):self.select()
 def test_historical_out_of_order_and_late_jobs_refuse(self):
  self.v['jobs'][1]['time_started']['$date']=self.epoch(0,50)*1000
  with self.assertRaises(RuntimeError):self.select()
if __name__=='__main__':unittest.main()
