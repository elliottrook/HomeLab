"""Offline predicate fixtures only; never creates an actual closure or gate pass."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).parent/'model-trial-20261106-r3/b60_exclusive_card_bridge.py'
class ClosureContractTests(unittest.TestCase):
 def setUp(self):
  s=importlib.util.spec_from_file_location('closure_predicate_fixture',P);self.m=importlib.util.module_from_spec(s);s.loader.exec_module(self.m)
  m=self.m;packet={'schema':'b60-post-xe-known-answer-packet.v1','state':'passed','attempted_requests':3,'retries':0,'records':[{'request':i,'predicate_passed':True,'outcome':'passed','http_status':200,'finish_reason':'stop'} for i in (1,2,3)]}
  self.post={'schema':'b60-post-xe-independent-postcheck.v1','booking_id':'b60-exclusive-20261106-day-r3','original_incident_sha256':m.INCIDENT_SHA,'production_restored':True,'unit_states_match_entry':True,'persistent_mount_identity_matches':True,'candidate_scope_empty':True,'news_mount_preserved':True,'manual_assistance_required':False,'deadline_missed':False,'trial_failed':False,'temporary_deny_gates':0,'booking_state':'complete','booking_result_code':'RESTORED','all_five_checkpoint_verifications':{g:True for g in ('104','110','114','115','116')},'answers':packet,'source_sha256':m.QUALIFICATION_SOURCE,'finished_epoch':100,'kernel':{'since_epoch':1794002064,'observed_epoch':200,'new_hazards':0},'qualification_terminal':{'qualified':True,'session_outcome':'complete-restored','incident_sha256':m.INCIDENT_SHA,'answers_sha256':hashlib.sha256(m.canonical(packet)).hexdigest(),'source_sha256':m.QUALIFICATION_SOURCE}}
  self.closure={'schema':'b60-device-incident-closure.v1','state':'CLOSED_FOR_ACCEPTED_SYCL_CONTINUATION','incident_id':m.INCIDENT,'original_open_sha256':m.INCIDENT_SHA,'qualification_booking_id':'b60-exclusive-20261106-day-r3','postcheck_sha256':'a'*64,'accepted_epoch':201,'acceptance_source_sha256':m.ACCEPTANCE_SOURCE_SHA}
 def test_bool_only_health_and_new_fault_cannot_close(self):
  for key,value in [('production_restored',False),('trial_failed',True),('answers',{'state':'passed'}),('source_sha256',{}),('all_five_checkpoint_verifications',{})]:
   p=copy.deepcopy(self.post);p[key]=value
   with self.assertRaises(RuntimeError):self.m.validate_incident_closure(self.closure,p)
  p=copy.deepcopy(self.post);p['kernel']['new_hazards']=1
  with self.assertRaises(RuntimeError):self.m.validate_incident_closure(self.closure,p)
 def test_incomplete_wrong_answer_and_assistance_refused(self):
  for k,v in [('finish_reason','length'),('predicate_passed',False)]:
   p=copy.deepcopy(self.post);p['answers']['records'][0][k]=v
   with self.assertRaises(RuntimeError):self.m.validate_incident_closure(self.closure,p)
  p=copy.deepcopy(self.post);p['manual_assistance_required']=True
  with self.assertRaises(RuntimeError):self.m.validate_incident_closure(self.closure,p)
 def test_original_open_hash_cannot_be_relabelled(self):
  c=copy.deepcopy(self.closure);c['original_open_sha256']='0'*64
  with self.assertRaises(RuntimeError):self.m.validate_incident_closure(c,self.post)
 def test_fixed_predicate_requires_all_fixture_fields(self):
  self.assertTrue(self.m.validate_incident_closure(self.closure,self.post))
if __name__=='__main__':unittest.main()
