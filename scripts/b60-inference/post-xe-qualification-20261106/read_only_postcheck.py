"""Independent read-only fixed-trial reconciliation after actual owner release.

Not installed in the four-file effect package. No restore, _load, model call,
mount, reset, lease or timer operation exists here. Raw checkpoints stay local.
"""
import hashlib,json,sys,time,subprocess
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session')
EXTRA=BASE.parent/'post-xe-qualification-20261106';ROOT=Path('/var/lib/local-ai-lab');B='b60-exclusive-20261106-day-r3'
sys.path[:0]=[str(EXTRA),str(BASE)]
from qualification import initialize,context,kernel,validate_packet
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes
from lab_hours_exclusive_session import canonical

def command(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=30);assert p.returncode==0;return p.stdout.strip()

def postcheck():
 with host_exclusion(ROOT):
  assert not any(p.exists() or p.is_symlink() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
  assert json.loads(command(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
  manifest=initialize();card=json.loads(protected_bytes(ROOT/'post-xe-cards'/(B+'.json')))
  history_raw=protected_bytes(ROOT/'backup-chain-history'/(B+'.json'))
  assert hashlib.sha256(history_raw).hexdigest()==card['backup_history_sha256']
  current_arm=json.loads(protected_bytes(ROOT/'arming-receipts'/(B+'-post-xe.json')))
  assert current_arm['source_sha256']==manifest and current_arm['card_sha256']==hashlib.sha256(protected_bytes(ROOT/'post-xe-cards'/(B+'.json'))).hexdigest()
  profile,store,bookings,scopes,adapter=context(B)
  for kind in ('owner','guardian'):
   fields=dict(l.split('=',1) for l in command(['systemctl','show','b60-exclusive-'+kind+'-'+B+'.service','--property=ActiveState,MainPID,TasksCurrent']).splitlines())
   assert fields['ActiveState'] in {'inactive','failed'} and fields['MainPID']=='0' and fields['TasksCurrent'] in {'0','','[not set]'}
  state=store.read('session.json');entry=store.read('entry.json');adapter.private=store.read('adapter.json');row=bookings.get(B)
  assert state['phase']=='released' and state['production_restored'] is True and state['deadline_missed'] is False and not state.get('manual_assistance_required',False)
  assert state['entry_sha256']==row['entry_sha256']==hashlib.sha256(canonical(entry)).hexdigest()
  assert row['state'] in {'complete','failed'} and row['result_code'] in {'RESTORED','FAILED_RESTORED'} and row['finished_epoch']<row['end_epoch']
  assert json.loads(protected_bytes(ROOT/'exclusive-releases'/(B+'.json')))==adapter.private['binding']
  deadline=int(time.time())+480
  mount=adapter._mount_identity(deadline)==adapter.private['mount_identity']
  units=adapter.units.verify(adapter.private['units'],deadline)
  guests={g:adapter._guest(g,'verify',deadline).get('verified') is True for g in profile['guest_plans']}
  assert mount and units and all(guests.values())
  MOUNT_SHA='640906303474d1a7f7ed527bb8ea5bcba74390af8c8dfcb105fdc12f7642825e'
  mount_rows=[l for l in command(['pct','config','110','--current']).splitlines() if l.startswith('mp0:')]
  assert len(mount_rows)==1 and hashlib.sha256(mount_rows[0].encode()).hexdigest()==MOUNT_SHA
  timers={}
  for r in adapter.private['units']:
   assert r['enablement'] not in {'masked','masked-runtime'}
   if r['unit'].endswith('.timer'):
    raw=command(['pct','exec',r['guest'],'--','systemctl','show',r['unit'],'--property=ActiveState,SubState,NextElapseUSecRealtime,NextElapseUSecMonotonic,LastTriggerUSec'])
    v=dict(l.split('=',1) for l in raw.splitlines());timers[r['guest']+'/'+r['unit']]=v
    if r['active']=='active':assert v['ActiveState']=='active' and v['SubState']=='waiting'
  count=command(['pct','exec','115','--','python3','-B','-c',"from pathlib import Path;print(len(list(Path('/run/systemd/system/paperless-summary.service.d').glob('90-b60-no-replay-*.conf'))))"]);assert count=='0'
  raw=command(['pct','exec','110','--','systemctl','show','b60-exclusive-trial-'+B+'.service','--property=LoadState,ActiveState,MainPID,TasksCurrent'])
  candidate=dict(l.split('=',1) for l in raw.splitlines());assert candidate.get('MainPID')=='0' and candidate.get('TasksCurrent') in {'0','','[not set]'}
  terminal=store.read('post-xe-terminal.json');answers=validate_packet(store.read('qualification-answers.json'))
  assert terminal['qualified'] is True and terminal['source_sha256']==manifest and terminal['incident_sha256']==card['incident_sha256']
  assert terminal['answers_sha256']==hashlib.sha256(canonical(answers)).hexdigest() and answers['state']=='passed'
  assert state['trial_failed'] is False and row['state']=='complete' and row['result_code']=='RESTORED'
  after=kernel(adapter,deadline,1794002064)
  from full_inference_lab_runtime import _gpu_users
  holders=_gpu_users();assert len(holders)==1 and next(iter(holders)).cgroup.endswith('/lxc/110/ns/system.slice/aster-llama.service')
  # Production probe checks the restored endpoint's health/identity; no generation.
  command(['pct','exec','110','--','/usr/local/sbin/aster-llama-production-auth-probe'])
  names=('admission.json','backup-history-admission.json','entry.json','adapter.json','session.json','qualification-preflight.json','qualification-intent.json','qualification-guardian-stop.json','qualification-effective-limits.json','qualification-residency.json','qualification-offload.json','qualification-answers.json','post-xe-terminal.json','entry-backend-start-intent.json','qualification-kernel-admission.json','qualification-kernel-before.json','qualification-kernel-after.json','unit-state-recovery.json')
  paths=[store.root/n for n in names]+[ROOT/'exclusive-releases'/(B+'.json'),ROOT/'reservations/records'/(B+'.json'),ROOT/'arming-receipts'/(B+'-post-xe.json'),ROOT/'post-xe-cards'/(B+'.json'),ROOT/'backup-chain-history'/(B+'.json')]
  hashes={str(p.relative_to(ROOT)):hashlib.sha256(protected_bytes(p,maximum=262144)).hexdigest() for p in paths if p.exists()}
  assert not (store.root/'qualification-guardian-stop.json').exists()
  result={'schema':'b60-post-xe-independent-postcheck.v1','booking_id':B,'observed_epoch':int(time.time()),'entry_sha256':state['entry_sha256'],'production_restored':True,'manual_assistance_required':False,'deadline_missed':False,'trial_failed':False,'booking_state':row['state'],'booking_result_code':row['result_code'],'finished_epoch':row['finished_epoch'],'all_five_checkpoint_verifications':guests,'unit_states_match_entry':units,'persistent_mount_identity_matches':mount,'candidate_scope_empty':True,'temporary_deny_gates':0,'news_mount_preserved':True,'scheduled_work_restored':timers,'source_sha256':manifest,'record_sha256':hashes,'answers':answers,'qualification_terminal':terminal,'kernel':after,'original_incident_sha256':card['incident_sha256'],'capability_latency_milestone_accepted':False}
  return result
if __name__=='__main__':
 try:print(json.dumps(postcheck(),sort_keys=True))
 except Exception as e:
  import traceback
  frames=[{'source_file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(e.__traceback__)]
  print(json.dumps({'state':'postcheck-no-go','failure_type':type(e).__name__,'source_frames':frames}));raise SystemExit(1)
