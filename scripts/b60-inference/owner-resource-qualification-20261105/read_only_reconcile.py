"""Fixed-field status/postcheck; no recovery, model probe or timer effects."""
import argparse,json,sys,time,hashlib,subprocess
from pathlib import Path
BINDINGS={'owner-loss':'b60-exclusive-20261105-day-r4','resource':'b60-exclusive-20261105-day-r5'}
ROOT=Path('/var/lib/local-ai-lab');P=Path('/usr/local/libexec/local-ai-lease/exclusive-session');EXTRA=P.parent/'recovery-qualification-20261105'
BASE='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2';WRAPPER='4a60b0e50b1f8bc58033fd33a005ec5ee173baaae2cffe3423f179ecfdd7a003'
def command(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=20);assert p.returncode==0;return p.stdout

def status(mode):
 b=BINDINGS[mode];out={'booking_id':b,'mode':mode,'observed_epoch':int(time.time()),'markers':{n:(ROOT/n).exists() for n in ('lease.json','lease.lock','full-inference-drain.json','full-inference-drain.lock')},'operation_marker':Path('/run/local-ai-lab-operation.lock').exists()}
 for label,path in [('session',ROOT/'exclusive-sessions'/b/'session.json'),('booking',ROOT/'reservations/records'/(b+'.json')),('qualification',ROOT/'exclusive-sessions'/b/'qualification-terminal.json')]:
  if path.exists():
   v=json.loads(path.read_bytes());out[label]={k:v[k] for k in ('phase','state','owner','booking_id','qualified','production_restored','trial_failed','deadline_missed','manual_assistance_required','finished_epoch','result_code') if k in v}
 for kind in ('owner','guardian'):
  raw=command(['systemctl','show','b60-exclusive-'+kind+'-'+b+'.service','--property=LoadState,ActiveState,SubState,MainPID,TasksCurrent,Result,ExecMainStatus'])
  out[kind]=dict(l.split('=',1) for l in raw.splitlines())
 return out

def postcheck(mode):
 sys.path[:0]=[str(P),str(EXTRA)]
 from host_exclusion import host_exclusion
 from lab_hours_exclusive_cli import context
 from lab_hours_exclusive_profile import protected_bytes
 from lab_hours_exclusive_session import canonical
 from b60_recovery_qualification import owner_loss_verdict
 b=BINDINGS[mode]
 with host_exclusion(ROOT):
  assert not any(p.exists() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
  assert json.loads(command(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
  profile,store,bookings,scopes,adapter=context(b);state=store.read('session.json');entry=store.read('entry.json');adapter.private=store.read('adapter.json');booking=bookings.get(b);terminal=store.read('qualification-terminal.json')
  assert terminal['mode']==mode and terminal['booking_id']==b and terminal['qualified'] is True and terminal['source_map_sha256']==BASE
  assert state['phase']=='released' and state['production_restored'] is True and state['deadline_missed'] is False and not state.get('manual_assistance_required',False)
  assert state['entry_sha256']==booking['entry_sha256']==hashlib.sha256(canonical(entry)).hexdigest()
  assert booking['finished_epoch']<booking['end_epoch']
  assert json.loads(protected_bytes(ROOT/'exclusive-releases'/(b+'.json')))==adapter.private['binding']
  pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in P.glob('*.py')}
  assert len(pins)==30 and hashlib.sha256(canonical(pins)).hexdigest()==BASE and profile['source_sha256']==pins
  assert hashlib.sha256(protected_bytes(EXTRA/'b60_recovery_qualification.py',executable=True)).hexdigest()==WRAPPER
  arm=json.loads(protected_bytes(ROOT/'arming-receipts'/(b+'-revision2.json')));assert arm['supplementary_source']['b60_recovery_qualification.py']==WRAPPER
  if mode=='owner-loss':
   assert terminal['qualification_source_sha256']==WRAPPER
   assert owner_loss_verdict(store.read('qualification-intent.json'),store.read('qualification-loss-observed.json'),store.read('qualification-fence.json'),state,booking)
  else:
   assert booking['state']=='complete' and booking['result_code']=='RESTORED' and state['trial_failed'] is False
   assert terminal['resource_limits_restored'] is True and terminal['trial_scope_empty'] is True
   base=store.read('resource-baseline.json')['properties'];now=dict(l.split('=',1) for l in command(['pct','exec','116','--','systemctl','show','epub-narration-worker.service','--property=CPUQuotaPerSecUSec,MemoryMax']).splitlines())
   assert now=={k:base[k] for k in ('CPUQuotaPerSecUSec','MemoryMax')}
   assert store.read('resource-namespace-restored.json')=={'global_probe_mount_absent':True,'global_probe_directory_absent':True}
  deadline=int(time.time())+480
  mount=adapter._mount_identity(deadline)==adapter.private['mount_identity'];units=adapter.units.verify(adapter.private['units'],deadline)
  guests={g:adapter._guest(g,'verify',deadline).get('verified') is True for g in profile['guest_plans']}
  assert mount and units and all(guests.values())
  assert all(r['enablement'] not in ('masked','masked-runtime') for r in adapter.private['units'])
  gate=command(['pct','exec','115','--','python3','-B','-c',"from pathlib import Path;print(len(list(Path('/run/systemd/system/paperless-summary.service.d').glob('90-b60-no-replay-*.conf'))))"]).strip();assert gate=='0'
  names=('admission.json','entry.json','session.json','adapter.json','qualification-terminal.json','qualification-intent.json','qualification-guardian-arm.json','qualification-loss-observed.json','qualification-fence.json','resource-headroom.json','resource-baseline.json','resource-limit-effect.json','resource-trial.json','resource-namespace-restored.json','unit-state-recovery.json')
  paths=[store.root/n for n in names]+[ROOT/'exclusive-releases'/(b+'.json'),ROOT/'reservations/records'/(b+'.json'),ROOT/'exclusive-integrity'/b/'terminal.json',ROOT/'arming-receipts'/(b+'-revision2.json')]
  hashes={str(p.relative_to(ROOT)):hashlib.sha256(protected_bytes(p,maximum=262144)).hexdigest() for p in paths if p.exists()}
  out={'schema':'b60-owner-resource-postcheck.v1','booking_id':b,'mode':mode,'qualified':True,'observed_epoch':int(time.time()),'qualification_terminal':terminal,'booking':{k:booking[k] for k in ('state','result_code','claimed_epoch','finished_epoch','start_epoch','end_epoch')},'session':{k:state[k] for k in ('phase','production_restored','trial_failed','deadline_missed','updated_epoch')},'manual_assistance_required':state.get('manual_assistance_required',False),'entry_sha256':state['entry_sha256'],'mount_identity_matches':mount,'unit_states_match_entry':units,'guest_checkpoints_verify':guests,'source_map_sha256':BASE,'qualification_source_sha256':WRAPPER,'record_sha256':hashes,'temporary_gate_count':0,'runtime_masks_present':False,'new_model_or_health_probe_executed':False}
  if mode=='owner-loss':out['fault_evidence']={n:store.read(n) for n in ('qualification-intent.json','qualification-guardian-arm.json','qualification-loss-observed.json','qualification-fence.json')}
  else:out['resource_evidence']={n:store.read(n) for n in ('resource-headroom.json','resource-baseline.json','resource-limit-effect.json','resource-trial.json','resource-namespace-restored.json')}
  return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=('status','postcheck'));p.add_argument('--mode',choices=tuple(BINDINGS),required=True);a=p.parse_args()
 try:print(json.dumps((status if a.action=='status' else postcheck)(a.mode),sort_keys=True))
 except Exception as error:print(json.dumps({'state':'postcheck-not-complete','error_type':type(error).__name__}));raise SystemExit(1)
