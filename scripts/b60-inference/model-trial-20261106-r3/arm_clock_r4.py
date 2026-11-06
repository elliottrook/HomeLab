"""Arm only the existing reviewed future model clock; no trial effect."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');sys.path.insert(0,str(BASE))
ROOT=Path('/var/lib/local-ai-lab');B='b60-exclusive-20261106-day-r4';PACKAGE=BASE.parent/'model-trial-20261106-r3'
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes,load_profile
from lab_hours_exclusive_session import canonical
from lab_hours_reservations import ReservationStore
from retained_archive_integrity import load_root_owned,verify,fixed_proxmox_inventory,fixed_resolve
def call(a,timeout=30):
 p=subprocess.run(a,capture_output=True,text=True,timeout=timeout);assert p.returncode==0;return p.stdout.strip()
def create(p,raw):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
with host_exclusion(ROOT):
 assert not any((ROOT/n).exists() or (ROOT/n).is_symlink() for n in ('lease.json','lease.lock','full-inference-drain.json','full-inference-drain.lock')) and not Path('/run/local-ai-lab-operation.lock').exists()
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 bookings=ReservationStore(ROOT/'reservations',expected_uid=0);row=bookings.get(B)
 assert row['state']=='reserved' and row['workload']=='b60-qwen36-35b-failure-capture-v1' and row['start_epoch']==1794013800 and row['end_epoch']==1794016500 and time.time()+120<row['start_epoch']
 assert not any(v.get('state')=='claimed' for v in bookings.list())
 raw=call(['systemctl','list-units','--all','--no-legend','--plain','aster-local-ai-pilot-owner-*','aster-local-ai-pilot-guardian-*','b60-exclusive-owner-*','b60-exclusive-guardian-*']);assert not any(len(l.split())>3 and l.split()[2] in {'active','activating','deactivating'} for l in raw.splitlines())
 assert not (ROOT/'exclusive-dispatch'/(B+'.json')).exists() and not (ROOT/'exclusive-sessions'/B).exists()
 integration=json.loads(protected_bytes(ROOT/'integration-receipts'/(B+'-model-inactive.json')))
 sys.path.insert(0,str(PACKAGE));from model_trial import initialize;assert initialize()==integration['source_sha256']
 profile_raw=protected_bytes(ROOT/'exclusive-activations'/(B+'.json'));assert hashlib.sha256(profile_raw).hexdigest()==integration['activation_sha256'];profile=load_profile(ROOT/'exclusive-activations'/(B+'.json'),BASE);assert profile['trial_seconds']==1200
 card_raw=protected_bytes(ROOT/'model-trial-cards'/(B+'.json'));assert hashlib.sha256(card_raw).hexdigest()==integration['model_card_sha256']
 cmd="from pathlib import Path;import sys;sys.path.insert(0,"+repr(str(BASE.parent/'full-inference-pilot'))+");import lab_hours_reserved_runner as r;r.load_manifest();import lab_hours_workloads as w;w.validate_registry();w.validate_inactive_target(Path("+repr(str(BASE.parent/'full-inference-pilot'))+"),workload_id='b60-qwen36-35b-failure-capture-v1')"
 call(['/usr/bin/python3','-B','-c',cmd])
 closed="import sys,json;sys.path.insert(0,"+repr(str(BASE.parent/'full-inference-pilot'))+");from b60_exclusive_card_bridge import require_incident_closed;print(json.dumps(require_incident_closed()))"
 closure=json.loads(call(['/usr/bin/python3','-B','-c',closed]));assert closure==integration['source_bound_incident_closure']
 proof=verify(load_root_owned(),fixed_proxmox_inventory(),date='2026_11_06',now_epoch=row['start_epoch']+120,resolve=fixed_resolve,lstat=os.lstat)
 history=protected_bytes(ROOT/'backup-chain-history'/(B+'.json'));assert hashlib.sha256(history).hexdigest()==json.loads(card_raw)['backup_history_sha256'] and 0<=row['start_epoch']+120-json.loads(history)['observed_epoch']<=7200
 name='b60-model-trial-'+B;units=Path('/etc/systemd/system')
 for suffix in ('timer','service'):assert hashlib.sha256(protected_bytes(units/(name+'.'+suffix),executable=True)).hexdigest()==integration['unit_sha256'][name+'.'+suffix]
 assert subprocess.run(['systemctl','is-enabled',name+'.timer'],capture_output=True,text=True).stdout.strip()=='disabled'
 fields=dict(l.split('=',1) for l in call(['systemctl','show',name+'.service','--property=ActiveState,MainPID']).splitlines());assert fields=={'ActiveState':'inactive','MainPID':'0'}
 obj='/org/freedesktop/systemd1/unit/'+''.join(c if c.isalnum() else '_'+format(ord(c),'02x') for c in name+'.timer')
 def prop(key):
  kind,v=call(['busctl','get-property','org.freedesktop.systemd1',obj,'org.freedesktop.systemd1.Timer',key]).split();assert kind=='t';return int(v)
 assert prop('LastTriggerUSec')==0
 audit=ROOT/'readiness-reviews';audit.mkdir(mode=0o700,exist_ok=True);assert hashlib.sha256(REVIEW_BYTES).hexdigest()==REVIEW_SHA256;create(audit/(B+'-model.json'),REVIEW_BYTES)
 assert time.time()+120<row['start_epoch'] and not (ROOT/'arming-receipts'/(B+'-model.json')).exists()
 call(['systemctl','enable','--now',name+'.timer'])
 assert subprocess.run(['systemctl','is-enabled',name+'.timer'],capture_output=True,text=True).stdout.strip()=='enabled'
 fields=dict(l.split('=',1) for l in call(['systemctl','show',name+'.timer','--property=ActiveState,SubState']).splitlines());assert fields=={'ActiveState':'active','SubState':'waiting'}
 assert prop('LastTriggerUSec')==0 and prop('NextElapseUSecRealtime')==1794013800000000
 fields=dict(l.split('=',1) for l in call(['systemctl','show',name+'.service','--property=ActiveState,MainPID']).splitlines());assert fields=={'ActiveState':'inactive','MainPID':'0'}
 receipt={'schema':'b60-model-trial-arming.v1','booking_id':B,'armed_epoch':int(time.time()),'start_epoch':row['start_epoch'],'end_epoch':row['end_epoch'],'recovery_reserve_until_epoch':row['end_epoch']+900,'model_card_sha256':integration['model_card_sha256'],'source_sha256':integration['source_sha256'],'activation_sha256':integration['activation_sha256'],'unit_sha256':integration['unit_sha256'],'independent_readiness_sha256':hashlib.sha256(REVIEW_BYTES).hexdigest(),'retained_archive_receipt':proof,'timer_enabled':True,'timer_active':'waiting','next_elapse_usec_realtime':prop('NextElapseUSecRealtime'),'last_trigger_usec':0,'launcher_inactive':True,'model_calls':0,'qualified':False,'source_bound_incident_closure':closure}
 create(ROOT/'arming-receipts'/(B+'-model.json'),canonical(receipt));print(json.dumps(receipt,sort_keys=True))
