"""Fixed minimal booking/status observer; no lease, stack or GPU call."""
import hashlib,json,subprocess,time
from pathlib import Path
R=Path('/var/lib/local-ai-lab');B='b60-exclusive-20261106-day-r3';S=R/'exclusive-sessions'/B
out={'epoch':int(time.time()),'booking_id':B,'markers':{n:(R/n).exists() for n in ('lease.json','lease.lock','full-inference-drain.json','full-inference-drain.lock')},'operation_marker':Path('/run/local-ai-lab-operation.lock').exists()}
rows=[json.loads(p.read_text()) for p in (R/'reservations/records').glob('*.json')]
out['claimed_bookings']=[{k:v.get(k) for k in ('booking_id','owner','claimant','start_epoch','end_epoch')} for v in rows if v.get('state')=='claimed']
v=next(v for v in rows if v['booking_id']==B);out['booking']={k:v.get(k) for k in ('state','workload','claimant','claimed_epoch','finished_epoch','result_code','entry_sha256')}
for name,keys in {'session.json':('phase','trial_deadline','restore_deadline','production_restored','deadline_missed','manual_assistance_required','trial_failed'),'qualification-answers.json':('state','planned_requests','attempted_requests','retries','records'),'post-xe-terminal.json':('qualified','session_outcome','finished_epoch','answers_sha256'),'qualification-owner-failure.json':('failure_type','observed_epoch'),'qualification-guardian-stop.json':('new_fault_or_monitor_failure','observed_epoch')}.items():
 p=S/name
 if p.exists():
  raw=p.read_bytes();v=json.loads(raw);out[name]={'sha256':hashlib.sha256(raw).hexdigest(),**{k:v.get(k) for k in keys}}
for kind in ('owner','guardian'):
 p=subprocess.run(['systemctl','show','b60-exclusive-'+kind+'-'+B+'.service','--property=LoadState,ActiveState,MainPID,TasksCurrent'],capture_output=True,text=True,timeout=5)
 out[kind]={'exit_code':p.returncode,'properties':dict(l.split('=',1) for l in p.stdout.splitlines())}
print(json.dumps(out,sort_keys=True))
