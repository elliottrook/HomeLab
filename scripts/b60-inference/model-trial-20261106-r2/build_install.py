"""Install one distinct R2 using pinned authenticated history and real integrity.

No existing model/card/clock is replaced. An unclaimed failed R1 reservation is
cancelled only after proving no owner, session, lease or stack effect occurred.
"""
import base64,hashlib,json
from pathlib import Path
here=Path(__file__).resolve().parent
names=('model_trial.py','namespace_mount.py','fixed_command.py','guest_requests.py','guest_supervisor.py','backup_chain_history.py')
manifest={n:hashlib.sha256((here/n).read_bytes()).hexdigest() for n in names}
files={n:base64.b64encode((here/n).read_bytes()).decode() for n in names}
history=Path('/private/tmp/b60-truenas-history-r2-receipt.json').read_bytes();history_sha=hashlib.sha256(history).hexdigest()
script=r'''
import base64,hashlib,json,os,sys,time,subprocess
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');sys.path.insert(0,str(BASE))
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes,load_profile
from lab_hours_exclusive_session import canonical
from lab_hours_reservations import ReservationStore
from retained_archive_integrity import load_root_owned,verify,fixed_proxmox_inventory,fixed_resolve
ROOT=Path('/var/lib/local-ai-lab');DEST=BASE.parent/'model-trial-20261106-r2';B='b60-exclusive-20261106-day-r2';OLD='b60-exclusive-20261106-day-r1'
def call(c,timeout=30):
 p=subprocess.run(c,capture_output=True,text=True,timeout=timeout);assert p.returncode==0;return p.stdout.strip()
def create(p,data,mode=0o600):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,mode)
 with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
with host_exclusion(ROOT):
 assert not any(p.exists() or p.is_symlink() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 oldroot=ROOT/'exclusive-sessions'/OLD;assert not (oldroot/'session.json').exists() and not (oldroot/'model-intent.json').exists()
 failure=json.loads(protected_bytes(oldroot/'admission-failure.json'));assert failure['failure_code']=='FRESH_BACKUP_SOURCE_TASK_CHAIN_FAILED' and failure['admitted'] is False
 for kind in ('owner','guardian'):
  v=dict(l.split('=',1) for l in call(['systemctl','show','b60-exclusive-'+kind+'-'+OLD+'.service','--property=ActiveState,MainPID,TasksCurrent']).splitlines());assert v['ActiveState'] in {'failed','inactive'} and v['MainPID']=='0' and v['TasksCurrent'] in {'0','','[not set]'}
 terminal={'schema':'b60-model-preclaim-no-go.v1','booking_id':OLD,'state':'NO_GO_BEFORE_CLAIM','failure_code':failure['failure_code'],'no_model_called':True,'no_stack_drain':True,'no_lease_claim':True,'observed_epoch':int(time.time()),'admission_failure_sha256':hashlib.sha256(protected_bytes(oldroot/'admission-failure.json')).hexdigest()}
 create(oldroot/'model-attempt-terminal.json',canonical(terminal))
 bookings=ReservationStore(ROOT/'reservations',expected_uid=0);old=bookings.get(OLD);assert old['state']=='reserved';bookings.cancel(OLD)
 now=int(time.time());start=((now+600+59)//60)*60;end=start+2700;zone=ZoneInfo('America/Vancouver');day=datetime.fromtimestamp(start,zone);finish=datetime.fromtimestamp(end+900,zone)
 assert day.strftime('%Y%m%d')=='20261106' and day.date()==finish.date() and day.strftime('%H:%M:%S')>='07:30:00' and finish.strftime('%H:%M:%S')<'15:45:00'
 row=bookings.reserve(booking_id=B,owner='b60-stream-a',start_epoch=start,end_epoch=end,exclusive=True)
 assert not DEST.exists();DEST.mkdir(mode=0o700)
 for n,encoded in FILES.items():
  raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==MANIFEST[n];create(DEST/n,raw)
 create(DEST/'manifest.json',canonical(MANIFEST));sys.path.insert(0,str(DEST))
 from model_trial import initialize,context,card_for
 assert initialize()==MANIFEST
 # Verify authenticated metadata custody and pin it; no new observer privilege.
 hroot=ROOT/'backup-chain-history';hroot.mkdir(mode=0o700,exist_ok=True);assert hroot.stat().st_uid==0 and hroot.stat().st_mode&0o077==0
 raw=base64.b64decode(HISTORY);assert hashlib.sha256(raw).hexdigest()==HISTORY_SHA;create(hroot/(B+'.json'),raw)
 plans={}
 for g in ('104','110','114','115','116'):
  r=json.loads(call(['pct','exec',g,'--','python3','-B','/usr/local/libexec/local-ai-lease/entry-checkpoint/lab_hours_prepare_entry_plan.py','--guest-id',g,'--booking-id',B],60));assert r['state']=='prepared';plans[g]=r['plan_sha256']
 template=load_profile(ROOT/'exclusive-activations'/(OLD+'.json'),BASE);profile=dict(template,booking_id=B,guest_plans=plans,trial_seconds=1200);create(ROOT/'exclusive-activations'/(B+'.json'),canonical(profile));load_profile(ROOT/'exclusive-activations'/(B+'.json'),BASE)
 card={'schema':'b60-fixed-model-trial.v1','booking_id':B,'start_epoch':start,'end_epoch':end,'source_sha256':MANIFEST,'candidate_sha256':'671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7','base_source_map_sha256':'e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2','mode':'qwen36-35b-reasoning-compatibility-v1','backup_history_sha256':HISTORY_SHA}
 create(ROOT/'model-trial-cards'/(B+'.json'),canonical(card));assert card_for(B)==card
 # Actual retained scan age is preserved, never renewed by this read-only reuse.
 inventory=fixed_proxmox_inventory();receipt=load_root_owned();cycle=day.strftime('%Y_%m_%d');proof=verify(receipt,inventory,date=cycle,now_epoch=int(time.time()),resolve=fixed_resolve,lstat=os.lstat);verify(receipt,inventory,date=cycle,now_epoch=start+120,resolve=fixed_resolve,lstat=os.lstat)
 iroot=ROOT/'exclusive-integrity'/B;iroot.mkdir(mode=0o700)
 create(iroot/'terminal.json',canonical({'schema':'aster-exclusive-integrity-result.v1','booking_id':B,'state':'complete','finished_epoch':receipt['finished_epoch'],'archive_receipt':proof,'observed_epoch':int(time.time()),'reused_from_booking':OLD,'new_scan_performed':False,'ai_stack_effects':False}))
 # Rehearse the actual backup-only producer now. This performs no admission,
 # claim, model call or health probe. It retains separately labelled evidence.
 from backup_chain_history import backup
 from lab_hours_exclusive_session import SessionStore
 from lab_hours_exclusive_cli import runner
 class A:pass
 a=A();a.runner=runner;prestore=SessionStore(ROOT/'model-source-prechecks'/B,expected_uid=0)
 fd=prestore.lock()
 try:
  result=backup(a,prestore,card,date_prefix=cycle,lease_issued_epoch=int(time.time()));assert result.source_observed and result.integrity_verified
 finally:os.close(fd)
 units=Path('/etc/systemd/system');name='b60-model-trial-'+B
 files={name+'.service':'[Unit]\nDescription=B60 distinct source-bound model trial R2\n\n[Service]\nType=oneshot\nUser=root\nRestart=no\nKillMode=control-group\nTimeoutStartSec=30\nExecStart=/usr/bin/python3 -B '+str(DEST/'model_trial.py')+' launch --booking-id '+B+'\n',name+'.timer':'[Unit]\nDescription=B60 distinct booked model clock R2\n\n[Timer]\nOnCalendar='+day.strftime('%Y-%m-%d %H:%M:%S')+' America/Vancouver\nPersistent=false\nAccuracySec=1s\nRandomizedDelaySec=0\nUnit='+name+'.service\n\n[Install]\nWantedBy=timers.target\n'}
 assert time.time()+120<start and not any((units/n).exists() or (units/n).is_symlink() for n in files)
 for n,v in files.items():create(units/n,v.encode(),0o644)
 call(['systemd-analyze','verify',*[str(units/n) for n in files]]);call(['systemctl','daemon-reload']);call(['systemctl','enable','--now',name+'.timer'])
 arm={'schema':'b60-model-trial-arming.v2','booking_id':B,'start_epoch':start,'end_epoch':end,'recovery_reserve_until_epoch':end+900,'source_sha256':MANIFEST,'guest_plan_sha256':plans,'backup_history_sha256':HISTORY_SHA,'retained_scan_finished_epoch':receipt['finished_epoch'],'archive_receipt':proof,'model_card_sha256':hashlib.sha256(canonical(card)).hexdigest(),'activation_sha256':hashlib.sha256(canonical(profile)).hexdigest(),'unit_sha256':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in files.items()},'prepared_epoch':int(time.time()),'model_run_claimed':False,'original_attempt_preserved':OLD}
 create(ROOT/'arming-receipts'/(B+'-model.json'),canonical(arm));print(json.dumps({'receipt':arm,'sha256':hashlib.sha256(canonical(arm)).hexdigest()},sort_keys=True))
'''
output='FILES='+repr(files)+'\nMANIFEST='+repr(manifest)+'\nHISTORY='+repr(base64.b64encode(history).decode())+'\nHISTORY_SHA='+repr(history_sha)+'\n'+script
Path('/private/tmp/b60-model-trial-r2-install.py').write_text(output)
(here/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,separators=(',',':')))
print(json.dumps({'installer_sha256':hashlib.sha256(output.encode()).hexdigest(),'manifest':manifest,'history_sha256':history_sha},sort_keys=True))
