"""Build the fixed inactive restoration qualification; performs no LAN effects."""
import base64,hashlib,json,importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent
NAMES=('qualification.py','entry_recovery.py','fixed_command.py','backup_chain_history.py','guest_entry_scope.py')
files={n:(H/n).read_bytes() for n in NAMES};manifest={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}
sp=importlib.util.spec_from_file_location('new_reg',H/'build_registration.py');reg=importlib.util.module_from_spec(sp);sp.loader.exec_module(reg);reg.build()
rnames=('b60_entry_rescue_card_bridge.py','lab_hours_workloads.py','lab_hours_reserved_runner.py','lab_hours_release_manifest.json');rfiles={n:(reg.DEST/n).read_bytes() for n in rnames}
prev=dict(reg.PREDECESSORS);prev['lab_hours_release_manifest.json']=json.loads((reg.SOURCE/'release-snapshot.json').read_text())['sha256']
auth={'schema':'b60-stream-a-recovery-authorization.v1','source':'current user conversation','instructions':["Proceed with the owner-loss and resource qualification, book the next available lab hours and complete those gates under Stream A approval. Don't stop at another preparation milestone.","Finish the failure-capture integration, reconcile the News-XPU changes, and run the next guarded model trial in booked lab hours under Stream A approval. Keep going until you have an actual result."],'scope':'Necessary fixed owner-loss-after-healthy-entry-restart qualification of restoration correction; no inference request, candidate model, driver, backup schedule or production promotion.'}
canonical=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
history=Path('/private/tmp/b60-r6-history-receipt.json').read_bytes()
header='import base64,hashlib,json,os,sys,time,subprocess\nfrom pathlib import Path\n'
for key,value in {'FILES':{n:base64.b64encode(v).decode() for n,v in files.items()},'MANIFEST':manifest,'REG_FILES':{n:base64.b64encode(v).decode() for n,v in rfiles.items()},'REG_SHA':{n:hashlib.sha256(v).hexdigest() for n,v in rfiles.items()},'REG_PREDECESSORS':prev,'AUTH':base64.b64encode(canonical(auth)).decode(),'HISTORY':base64.b64encode(history).decode()}.items():header+=key+'='+repr(value)+'\n'
body='''
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');sys.path.insert(0,str(BASE))
ROOT=Path('/var/lib/local-ai-lab');DEST=BASE.parent/'entry-rescue-qualification-20261106-r6';B='b60-exclusive-20261106-day-r6'
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes,load_profile
from lab_hours_exclusive_session import canonical,SessionStore
from lab_hours_reservations import ReservationStore
from retained_archive_integrity import load_root_owned,verify,fixed_proxmox_inventory,fixed_resolve
def call(c,timeout=30):
 p=subprocess.run(c,capture_output=True,text=True,timeout=timeout);assert p.returncode==0;return p.stdout.strip()
def create(p,raw,mode=0o600):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,mode)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
'''+(H/'registration_install.py.txt').read_text()+'''
with host_exclusion(ROOT):
 assert not any((ROOT/n).exists() or (ROOT/n).is_symlink() for n in ('lease.json','lease.lock','full-inference-drain.json','full-inference-drain.lock')) and not Path('/run/local-ai-lab-operation.lock').exists()
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 bookings=ReservationStore(ROOT/'reservations',expected_uid=0);row=bookings.get(B)
 assert row['state']=='reserved' and row['owner']=='b60-stream-a' and row['kind']=='exclusive-stack' and row['workload'] is None and (row['start_epoch'],row['end_epoch'])==(1794016800,1794018600) and time.time()+120<row['start_epoch']
 assert not any(v.get('state')=='claimed' for v in bookings.list())
 assert set(bookings.check_window(start_epoch=row['start_epoch'],end_epoch=row['end_epoch']+900))=={B}
 scopes=call(['systemctl','list-units','--all','--no-legend','--plain','aster-local-ai-pilot-owner-*','aster-local-ai-pilot-guardian-*','b60-exclusive-owner-*','b60-exclusive-guardian-*']);assert not any(len(l.split())>3 and l.split()[2] in {'active','activating','deactivating'} for l in scopes.splitlines())
 assert not DEST.exists() and not (ROOT/'exclusive-sessions'/B).exists()
 for parent in ('exclusive-activations','entry-rescue-cards'):
  (ROOT/parent).mkdir(mode=0o700,exist_ok=True);assert not (ROOT/parent/(B+'.json')).exists()
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')};assert len(pins)==30 and hashlib.sha256(canonical(pins)).hexdigest()=='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
 prepraw=protected_bytes(ROOT/'integrity-preparation/b60-entry-rescue-preparation-20261106-r6-v2/terminal.json');prep=json.loads(prepraw);assert prep['state']=='complete' and prep['new_scan_performed'] is True
 proof=verify(load_root_owned(),fixed_proxmox_inventory(),date='2026_11_06',now_epoch=row['start_epoch']+120,resolve=fixed_resolve,lstat=os.lstat);assert proof==prep['archive_receipt']
 history=base64.b64decode(HISTORY);assert 0<=row['start_epoch']+120-json.loads(history)['observed_epoch']<=7200
 ns={'__name__':'inert_fixed_recovery_gate'};exec(compile(base64.b64decode(REG_FILES['b60_entry_rescue_card_bridge.py']),'b60_entry_rescue_card_bridge.py','exec'),ns);closure=ns['require_incident_closed']()
 registration=install_registration(bookings,row)
 DEST.mkdir(mode=0o700)
 for n,v in FILES.items():create(DEST/n,base64.b64decode(v))
 create(DEST/'manifest.json',canonical(MANIFEST));sys.path.insert(0,str(DEST));from qualification import initialize;assert initialize()==MANIFEST
 auth=base64.b64decode(AUTH);assert not (ROOT/'entry-rescue-authorization.json').exists();create(ROOT/'entry-rescue-authorization.json',auth)
 create(ROOT/'backup-chain-history'/(B+'.json'),history)
 code="from pathlib import Path;import os,base64,hashlib;d=Path('/usr/local/libexec/local-ai-lease/entry-rescue-qualification-20261106-r6');assert not d.exists();d.mkdir(mode=0o700);raw=base64.b64decode("+repr(FILES['guest_entry_scope.py'])+");fd=os.open(d/'guest_entry_scope.py',os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);f=os.fdopen(fd,'wb');f.write(raw);f.flush();os.fsync(f.fileno());f.close();print(hashlib.sha256(raw).hexdigest())"
 assert call(['pct','exec','116','--','python3','-B','-c',code])==MANIFEST['guest_entry_scope.py']
 plans={}
 for g in ('104','110','114','115','116'):
  command=['pct','exec',g,'--','python3','-B']+([str(DEST/'guest_entry_scope.py'),'prepare'] if g=='116' else ['/usr/local/libexec/local-ai-lease/entry-checkpoint/lab_hours_prepare_entry_plan.py'])+['--guest-id',g,'--booking-id',B]
  value=json.loads(call(command,60));assert value['state']=='prepared';plans[g]=value['plan_sha256']
 template=load_profile(ROOT/'exclusive-activations/b60-exclusive-20261106-day-r4.json',BASE);profile=dict(template,booking_id=B,guest_plans=plans,trial_seconds=600)
 create(ROOT/'exclusive-activations'/(B+'.json'),canonical(profile));load_profile(ROOT/'exclusive-activations'/(B+'.json'),BASE)
 card={'schema':'b60-entry-rescue-card.v1','booking_id':B,'start_epoch':row['start_epoch'],'end_epoch':row['end_epoch'],'source_sha256':MANIFEST,'incident_sha256':'7c1355adec390764cd970036233c1a70325d224b387e751dff4ef06db0e5cc6e','backup_history_sha256':hashlib.sha256(history).hexdigest(),'authorization_sha256':hashlib.sha256(auth).hexdigest()};create(ROOT/'entry-rescue-cards'/(B+'.json'),canonical(card))
 from backup_chain_history import backup
 from lab_hours_exclusive_cli import runner
 class A:pass
 a=A();a.runner=runner;store=SessionStore(ROOT/'entry-rescue-prechecks'/B,expected_uid=0);fd=store.lock()
 try:
  result=backup(a,store,card,date_prefix='2026_11_06',lease_issued_epoch=int(time.time()));assert result.source_observed and result.integrity_verified
 finally:os.close(fd)
 name='b60-entry-rescue-'+B;units=Path('/etc/systemd/system')
 files={name+'.service':'[Unit]\\nDescription=B60 fixed entry preservation qualification\\n\\n[Service]\\nType=oneshot\\nUser=root\\nRestart=no\\nKillMode=control-group\\nTimeoutStartSec=30\\nExecStart=/usr/bin/python3 -B '+str(BASE.parent/'full-inference-pilot/lab_hours_reserved_runner.py')+' --booking-id '+B+'\\n',name+'.timer':'[Unit]\\nDescription=B60 exact future entry preservation clock\\n\\n[Timer]\\nOnCalendar=2026-11-06 19:00:00 America/Vancouver\\nPersistent=false\\nAccuracySec=1s\\nRandomizedDelaySec=0\\nUnit='+name+'.service\\n\\n[Install]\\nWantedBy=timers.target\\n'}
 assert time.time()+120<row['start_epoch']
 for n,v in files.items():create(units/n,v.encode(),0o644)
 call(['systemctl','daemon-reload'])
 assert subprocess.run(['systemctl','is-enabled',name+'.timer'],capture_output=True,text=True).stdout.strip()=='disabled'
 assert dict(l.split('=',1) for l in call(['systemctl','show',name+'.service','--property=ActiveState,MainPID']).splitlines())=={'ActiveState':'inactive','MainPID':'0'}
 receipt={'schema':'b60-entry-rescue-integration.v1','booking_id':B,'state':'installed-inactive','start_epoch':row['start_epoch'],'end_epoch':row['end_epoch'],'source_sha256':MANIFEST,'guest_plan_sha256':plans,'activation_sha256':hashlib.sha256(canonical(profile)).hexdigest(),'model_card_sha256':hashlib.sha256(canonical(card)).hexdigest(),'backup_history_sha256':hashlib.sha256(history).hexdigest(),'integrity_preparation_terminal_sha256':hashlib.sha256(prepraw).hexdigest(),'archive_receipt':proof,'source_bound_incident_closure':closure,'global_registration_file_sha256':REG_SHA,'unit_sha256':{n:hashlib.sha256(v.encode()).hexdigest() for n,v in files.items()},'prepared_epoch':int(time.time()),'model_generation_calls':0,'clock_armed':False}
 create(ROOT/'integration-receipts'/(B+'-entry-rescue-inactive.json'),canonical(receipt));print(json.dumps({'receipt':receipt,'sha256':hashlib.sha256(canonical(receipt)).hexdigest()},sort_keys=True))
'''
script=header+body;compile(script,'fixed-inactive-install','exec');Path('/private/tmp/b60-r6-install.py').write_text(script);(H/'manifest.json').write_bytes(canonical(manifest));print(json.dumps({'installer_sha256':hashlib.sha256(script.encode()).hexdigest(),'source_sha256':manifest},sort_keys=True))
