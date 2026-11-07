"""Independent read-only fixed-trial reconciliation after actual owner release.

Not installed in the four-file effect package. No restore, _load, model call,
mount, reset, lease or timer operation exists here. Raw checkpoints stay local.
"""
import hashlib,json,sys,time,subprocess
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session')
EXTRA=BASE.parent/'entry-rescue-qualification-20261106-r7';ROOT=Path('/var/lib/local-ai-lab');B='b60-exclusive-20261106-day-r7'
sys.path[:0]=[str(EXTRA),str(BASE)]
from qualification import initialize,context,kernel
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes
from lab_hours_exclusive_session import canonical

def command(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=30);assert p.returncode==0;return p.stdout.strip()

def empty_unit(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=30);assert len(p.stdout)<=4096
 fields=dict(l.split('=',1) for l in p.stdout.splitlines())
 absent=p.returncode in {0,1} and fields.get('LoadState')=='not-found' and fields.get('ActiveState') in {None,'inactive','failed'} and fields.get('MainPID')=='0' and fields.get('TasksCurrent') in {None,'0','','[not set]'}
 empty=p.returncode==0 and fields.get('ActiveState') in {'inactive','failed'} and fields.get('MainPID')=='0' and fields.get('TasksCurrent') in {'0','','[not set]'}
 assert absent or empty
 return fields

def postcheck():
 with host_exclusion(ROOT):
  assert not any(p.exists() or p.is_symlink() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
  assert json.loads(command(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
  manifest=initialize();card=json.loads(protected_bytes(ROOT/'entry-rescue-cards'/(B+'.json')))
  history_raw=protected_bytes(ROOT/'backup-chain-history'/(B+'.json'))
  assert hashlib.sha256(history_raw).hexdigest()==card['backup_history_sha256']
  current_arm=json.loads(protected_bytes(ROOT/'arming-receipts'/(B+'-entry-rescue.json')))
  assert current_arm['source_sha256']==manifest and current_arm['model_card_sha256']==hashlib.sha256(protected_bytes(ROOT/'entry-rescue-cards'/(B+'.json'))).hexdigest()
  profile,store,bookings,scopes,adapter=context(B)
  for kind in ('owner','guardian'):
   fields=empty_unit(['systemctl','show','b60-exclusive-'+kind+'-'+B+'.service','--property=LoadState,ActiveState,MainPID,TasksCurrent'])
  state=store.read('session.json');entry=store.read('entry.json');adapter.private=store.read('adapter.json');row=bookings.get(B)
  activation_raw=protected_bytes(ROOT/'exclusive-activations'/(B+'.json'));assert hashlib.sha256(activation_raw).hexdigest()==current_arm['activation_sha256'] and profile==adapter.private['profile']
  actual_plan_hashes={g:command(['pct','exec',g,'--','sha256sum','/var/lib/local-ai-lab-entry/'+B+'/plan.json']).split()[0] for g in profile['guest_plans']};assert actual_plan_hashes==profile['guest_plans']
  assert state['phase']=='released' and state['production_restored'] is True and state['deadline_missed'] is False and not state.get('manual_assistance_required',False)
  assert state['entry_sha256']==row['entry_sha256']==hashlib.sha256(canonical(entry)).hexdigest()
  assert row['state'] in {'complete','failed'} and row['result_code'] in {'RESTORED','FAILED_RESTORED'} and row['finished_epoch']<row['end_epoch']
  assert json.loads(protected_bytes(ROOT/'exclusive-releases'/(B+'.json')))==adapter.private['binding']
  deadline=int(time.time())+480
  mount=adapter._mount_identity(deadline)==adapter.private['mount_identity']
  units=adapter.units.verify(adapter.private['units'],deadline)
  guests={g:adapter._guest(g,'verify',deadline).get('verified') is True for g in profile['guest_plans']}
  assert mount and units and all(guests.values())
  timers={}
  for r in adapter.private['units']:
   assert r['enablement'] not in {'masked','masked-runtime'}
   if r['unit'].endswith('.timer'):
    raw=command(['pct','exec',r['guest'],'--','systemctl','show',r['unit'],'--property=ActiveState,SubState,NextElapseUSecRealtime,NextElapseUSecMonotonic,LastTriggerUSec'])
    v=dict(l.split('=',1) for l in raw.splitlines());timers[r['guest']+'/'+r['unit']]=v
    if r['active']=='active':
     assert v['ActiveState']=='active' and v['SubState']=='waiting'
     object_path='/org/freedesktop/systemd1/unit/'+''.join(c if c.isalnum() else '_'+format(ord(c),'02x') for c in r['unit'])
     numeric={}
     for prop in ('NextElapseUSecRealtime','NextElapseUSecMonotonic'):
      kind,val=command(['pct','exec',r['guest'],'--','busctl','get-property','org.freedesktop.systemd1',object_path,'org.freedesktop.systemd1.Timer',prop]).split();assert kind=='t';numeric[prop]=int(val)
     guest_clock=json.loads(command(['pct','exec',r['guest'],'--','python3','-B','-c','import time,json;print(json.dumps({"realtime":time.time(),"monotonic":time.monotonic()}))']))
     assert (0<numeric['NextElapseUSecRealtime']<18446744073709551615 and numeric['NextElapseUSecRealtime']/1e6>guest_clock['realtime']) or (0<numeric['NextElapseUSecMonotonic']<18446744073709551615 and numeric['NextElapseUSecMonotonic']/1e6>guest_clock['monotonic'])
     v['numeric_next_elapse_usec']=numeric;v['guest_clock']=guest_clock
  count=command(['pct','exec','115','--','python3','-B','-c',"from pathlib import Path;print(len(list(Path('/run/systemd/system/paperless-summary.service.d').glob('90-b60-no-replay-*.conf'))))"]);assert count=='0'
  candidate=empty_unit(['pct','exec','110','--','systemctl','show','b60-exclusive-trial-'+B+'.service','--property=LoadState,ActiveState,MainPID,TasksCurrent'])
  client=empty_unit(['pct','exec','110','--','systemctl','show','b60-exclusive-client-'+B+'.service','--property=LoadState,ActiveState,MainPID,TasksCurrent'])
  terminal=store.read('qualification-terminal.json');preserve=store.read('entry-backend-preservation-proof.json');loss=store.read('qualification-owner-loss-intent.json');idempotent=store.read('entry-backend-idempotent-start.json')
  assert terminal['qualified'] is True and terminal['source_sha256']==manifest and terminal['model_generation_calls']==0 and terminal['additional_backend_start_calls']==0 and terminal['manual_assistance_required'] is False and terminal['all_crash_windows_qualified'] is False
  assert loss['after_first_accepted_start_and_health'] is True and loss['exit_status']==86 and idempotent['new_backend_start_invoked'] is False
  assert preserve['before']['main_pid']==preserve['after']['main_pid'] and preserve['before']['exec_main_start_usec']==preserve['after']['exec_main_start_usec'] and preserve['candidate_and_client_empty'] is True and preserve['other_consumers_quiescent'] is True
  native=dict(l.split('=',1) for l in command(['systemctl','show','b60-exclusive-owner-'+B+'.service','--property=ActiveState,MainPID,TasksCurrent,ExecMainCode,ExecMainStatus']).splitlines())
  assert native['ActiveState']=='failed' and native['MainPID']=='0' and native['TasksCurrent'] in {'0','','[not set]'} and native['ExecMainCode']=='1' and native['ExecMainStatus']=='86'
  backend=dict(l.split('=',1) for l in command(['pct','exec','110','--','systemctl','show','aster-llama.service','--property=MainPID,ExecMainStartTimestampMonotonic']).splitlines())
  assert backend['MainPID']==preserve['after']['main_pid'] and int(backend['ExecMainStartTimestampMonotonic'])==preserve['after']['exec_main_start_usec']
  assert state['trial_failed'] is True and row['state']=='failed' and row['result_code']=='FAILED_RESTORED'
  after=kernel(adapter,deadline,1794002064)
  from full_inference_lab_runtime import _gpu_users
  holders=_gpu_users();assert len(holders)==1 and next(iter(holders)).cgroup.endswith('/lxc/110/ns/system.slice/aster-llama.service')
  # Production probe checks the restored endpoint's health/identity; no generation.
  command(['pct','exec','110','--','/usr/local/sbin/aster-llama-production-auth-probe'])
  names=('admission.json','backup-history-admission.json','entry.json','adapter.json','session.json','qualification-intent.json','qualification-owner-loss-intent.json','entry-backend-start-intent.json','entry-backend-preservation-intent.json','entry-backend-preservation-proof.json','entry-backend-idempotent-start.json','qualification-kernel-before.json','qualification-terminal.json','unit-state-recovery.json')
  paths=[store.root/n for n in names]+[ROOT/'exclusive-dispatch'/(B+'.json'),ROOT/'exclusive-activations'/(B+'.json'),ROOT/'exclusive-releases'/(B+'.json'),ROOT/'reservations/records'/(B+'.json'),ROOT/'arming-receipts'/(B+'-entry-rescue.json'),ROOT/'entry-rescue-cards'/(B+'.json'),ROOT/'backup-chain-history'/(B+'.json')]

  hashes={str(p.relative_to(ROOT)):hashlib.sha256(protected_bytes(p,maximum=262144)).hexdigest() for p in paths if p.exists()}
  assert not (store.root/'qualification-guardian-stop.json').exists()
  result={'schema':'b60-entry-rescue-independent-postcheck.v1','booking_id':B,'observed_epoch':int(time.time()),'activation_sha256':hashlib.sha256(activation_raw).hexdigest(),'guest_plan_sha256':actual_plan_hashes,'entry_sha256':state['entry_sha256'],'production_restored':True,'manual_assistance_required':False,'deadline_missed':False,'trial_failed':True,'intended_fault_observed':True,'owner_exit_status':86,'model_generation_calls':0,'generation_count_scope':'qualification-owned API requests only','additional_backend_start_calls':0,'all_crash_windows_qualified':False,'booking_state':row['state'],'booking_result_code':row['result_code'],'finished_epoch':row['finished_epoch'],'all_five_checkpoint_verifications':guests,'unit_states_match_entry':units,'persistent_mount_identity_matches':mount,'candidate_scope_empty':True,'client_scope_empty':True,'temporary_deny_gates':0,'news_mount_preserved':True,'scheduled_work_restored':timers,'source_sha256':manifest,'record_sha256':hashes,'preservation_proof':preserve,'qualification_terminal':terminal,'kernel':after,'original_incident_sha256':card['incident_sha256'],'capability_latency_milestone_accepted':False}
  return result
if __name__=='__main__':
 try:print(json.dumps(postcheck(),sort_keys=True))
 except Exception as e:
  import traceback
  frames=[{'source_file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(e.__traceback__)]
  print(json.dumps({'state':'postcheck-no-go','failure_type':type(e).__name__,'source_frames':frames}));raise SystemExit(1)
