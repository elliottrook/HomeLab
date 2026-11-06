"""Build exact host installer bytes locally. Does not connect or run effects."""
import base64,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
names=('model_trial.py','namespace_mount.py','fixed_command.py','guest_requests.py')
manifest={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in names}
files={n:base64.b64encode((HERE/n).read_bytes()).decode() for n in names}
prefix='FILES='+repr(files)+'\nMANIFEST='+repr(manifest)+'\n'
installer=r'''
import base64,hashlib,json,os,subprocess,sys,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');sys.path.insert(0,str(BASE))
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes,load_profile
from lab_hours_reservations import ReservationStore
from lab_hours_exclusive_session import canonical
ROOT=Path('/var/lib/local-ai-lab');DEST=BASE.parent/'model-trial-20261106'
def call(c,timeout=30):
 p=subprocess.run(c,capture_output=True,text=True,timeout=timeout);assert p.returncode==0;return p.stdout.strip()
def create(path,data,mode=0o600):
 fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,mode)
 with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(path.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
with host_exclusion(ROOT):
 assert not any(p.exists() or p.is_symlink() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')}
 assert len(pins)==30 and hashlib.sha256(canonical(pins)).hexdigest()=='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
 prep=Path('/usr/local/libexec/local-ai-lease/b60-exclusive-integrity-b60-exclusive-20261105-day-r2/lab_hours_exclusive_integrity_prepare.py')
 raw=protected_bytes(prep,executable=True,maximum=262144);expected=PREP_SHA
 assert hashlib.sha256(raw).hexdigest()==expected
 assert not DEST.exists();DEST.mkdir(mode=0o700)
 for name,encoded in FILES.items():
  data=base64.b64decode(encoded);assert hashlib.sha256(data).hexdigest()==MANIFEST[name];create(DEST/name,data)
 create(DEST/'manifest.json',canonical(MANIFEST))
 sys.path.insert(0,str(DEST));from model_trial import initialize
 assert initialize()==MANIFEST
 # Guest workload installation does not call a model or read its key file.
 guestcode="from pathlib import Path;import os,base64;d=Path('/usr/local/libexec/local-ai-lease/model-trial-20261106');assert not d.exists();d.mkdir(mode=0o700);p=d/'guest_requests.py';fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);f=os.fdopen(fd,'wb');f.write(base64.b64decode("+repr(FILES['guest_requests.py'])+"));f.flush();os.fsync(f.fileno());f.close()"
 call(['pct','exec','110','--','python3','-B','-c',guestcode])
 assert call(['pct','exec','110','--','sha256sum','/usr/local/libexec/local-ai-lease/model-trial-20261106/guest_requests.py']).split()[0]==MANIFEST['guest_requests.py']
 # Exact fresh daytime booking; no existing reservation is modified.
 now=int(time.time());start=((now+3600+59)//60)*60;end=start+2700
 local=datetime.fromtimestamp(start,ZoneInfo('America/Vancouver'));finish=datetime.fromtimestamp(end+900,ZoneInfo('America/Vancouver'))
 assert local.strftime('%Y%m%d')=='20261106' and local.date()==finish.date() and local.strftime('%H:%M:%S')>='07:30:00' and finish.strftime('%H:%M:%S')<='22:00:00'
 booking='b60-exclusive-20261106-day-r1';store=ReservationStore(ROOT/'reservations',expected_uid=0)
 row=store.reserve(booking_id=booking,owner='b60-stream-a',start_epoch=start,end_epoch=end,exclusive=True)
 plans={}
 for guest in ('104','110','114','115','116'):
  r=json.loads(call(['pct','exec',guest,'--','python3','-B','/usr/local/libexec/local-ai-lease/entry-checkpoint/lab_hours_prepare_entry_plan.py','--guest-id',guest,'--booking-id',booking],60));assert r['state']=='prepared';plans[guest]=r['plan_sha256']
 template=load_profile(ROOT/'exclusive-activations/b60-exclusive-20261105-day-r5.json',BASE)
 profile=dict(template,booking_id=booking,trial_seconds=1200,guest_plans=plans)
 create(ROOT/'exclusive-activations'/(booking+'.json'),canonical(profile));load_profile(ROOT/'exclusive-activations'/(booking+'.json'),BASE)
 cards=ROOT/'model-trial-cards';cards.mkdir(mode=0o700,exist_ok=True);assert cards.stat().st_uid==0 and cards.stat().st_mode&0o077==0
 card={'schema':'b60-fixed-model-trial.v1','booking_id':booking,'start_epoch':start,'end_epoch':end,'source_sha256':MANIFEST,'candidate_sha256':'671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7','base_source_map_sha256':'e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2','mode':'qwen36-35b-reasoning-compatibility-v1'}
 create(cards/(booking+'.json'),canonical(card))
 # Pin exact already-reviewed daytime integrity producer, not the old nightly source.
 package=BASE.parent/('b60-exclusive-integrity-'+booking);package.mkdir(mode=0o700);create(package/'lab_hours_exclusive_integrity_prepare.py',raw)
 units=Path('/etc/systemd/system');files={}
 def clock(prefix,epoch,command):
  dt=datetime.fromtimestamp(epoch,ZoneInfo('America/Vancouver'))
  files[prefix+'.service']='[Unit]\nDescription=B60 exact booked model compatibility\n\n[Service]\nType=oneshot\nUser=root\nRestart=no\nKillMode=control-group\nTimeoutStartSec=1500\nNice=19\nIOSchedulingClass=idle\nExecStart='+command+'\n'
  files[prefix+'.timer']='[Unit]\nDescription=B60 exact date clock\n\n[Timer]\nOnCalendar='+dt.strftime('%Y-%m-%d %H:%M:%S')+' America/Vancouver\nPersistent=false\nAccuracySec=1s\nRandomizedDelaySec=0\nUnit='+prefix+'.service\n\n[Install]\nWantedBy=timers.target\n'
 clock('b60-exclusive-integrity-'+booking,start-3300,'/usr/bin/python3 -B '+str(package/'lab_hours_exclusive_integrity_prepare.py')+' --booking-id '+booking+' --self-sha256 '+expected)
 clock('b60-model-trial-'+booking,start,'/usr/bin/python3 -B '+str(DEST/'model_trial.py')+' launch --booking-id '+booking)
 assert start-3300>time.time()+120 and not any((units/n).exists() for n in files)
 for n,body in files.items():create(units/n,body.encode(),0o644)
 call(['systemd-analyze','verify',*[str(units/n) for n in files]])
 call(['systemctl','daemon-reload']);call(['systemctl','enable','--now',*[n for n in files if n.endswith('.timer')]])
 receipt={'schema':'b60-model-trial-arming.v1','booking_id':booking,'start_epoch':start,'end_epoch':end,'recovery_reserve_until_epoch':end+900,'source_sha256':MANIFEST,'base_source_sha256':pins,'guest_plan_sha256':plans,'model_card_sha256':hashlib.sha256(canonical(card)).hexdigest(),'activation_sha256':hashlib.sha256(canonical(profile)).hexdigest(),'unit_sha256':{n:hashlib.sha256(body.encode()).hexdigest() for n,body in files.items()},'integrity_source_sha256':expected,'prepared_epoch':int(time.time()),'model_run_claimed':False}
 create(ROOT/'arming-receipts'/(booking+'-model.json'),canonical(receipt));print(json.dumps(receipt,sort_keys=True))
'''
source=Path('/private/tmp/b60-resource-checkpoint-20261104/scripts/local-ai/b60_daytime_integrity_prepare.py').read_bytes()
output=prefix+'PREP_SHA='+repr(hashlib.sha256(source).hexdigest())+'\n'+installer
Path('/private/tmp/b60-model-trial-install.py').write_text(output)
(HERE/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,separators=(',',':')))
print(json.dumps({'manifest':manifest,'installer_sha256':hashlib.sha256(output.encode()).hexdigest(),'daytime_integrity_sha256':hashlib.sha256(source).hexdigest()}))
