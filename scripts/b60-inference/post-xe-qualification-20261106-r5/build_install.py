from pathlib import Path
import json,hashlib,base64,importlib.util
d=Path(__file__).resolve().parent;r=d.parent;reg=Path('/private/tmp/b60-post-xe-registration-20261106-r5');pred=d/'registry-predecessor'
files={n:(d/n).read_bytes() for n in ('qualification.py','fixed_command.py','known_answer_requests.py','backup_chain_history.py','guest_entry_scope.py')};manifest={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}
regfiles={n:(reg/n).read_bytes() for n in ('b60_post_xe_r5_card_bridge.py','lab_hours_workloads.py','lab_hours_reserved_runner.py','lab_hours_release_manifest.json')}
regsha={n:hashlib.sha256(v).hexdigest() for n,v in regfiles.items()};prev={n:hashlib.sha256((pred/n).read_bytes()).hexdigest() for n in ('lab_hours_workloads.py','lab_hours_reserved_runner.py','lab_hours_release_manifest.json')}
authority={'schema':'b60-standing-reservation-autonomy-receipt.v1','source':'native Codex read_thread','source_thread':'01a1b159-9ede-79f2-b83a-e86fd200c2e9','messages':[{'id':'01a1b2d2-65e1-7cc3-b935-8b93c5a7a681','text':'you cant wait for approval on this and you cannot set it up as 3 tries. the whole point is that you have full autonomous use of the lab. my approval has to be for any work relating to the reservation within the lab hours!'},{'id':'01a1b2f0-12b3-75a1-a3c0-802d810715da','text':'remember you are approved to autonomously fix and move on during the lab hours and stream a after that, so dont stop'}],'scope':'bounded structurally different accepted-SYCL known-answer qualification; no reset/reboot/driver change; original incident remains OPEN until independent actual acceptance','new_incident_specific_owner_approval_claimed':False}
canon=lambda v:json.dumps(v,sort_keys=True,separators=(',',':')).encode()
history=(r.parent.parent/'docs/projects/B60-Inference-Engineering/evidence/20261106-model-r3/r5-backup-history.json').read_bytes();assert hashlib.sha256(history).hexdigest()=='36adbf062e53ce15650ffca3d8be137edf4352f6cbf5c242ce2ab67fde576a8c'
header='import base64,hashlib,json,os,subprocess,sys,time\nfrom pathlib import Path\n'
for k,v in {'FILES':{n:base64.b64encode(x).decode() for n,x in files.items()},'MANIFEST':manifest,'REG_FILES':{n:base64.b64encode(x).decode() for n,x in regfiles.items()},'REG_SHA':regsha,'REG_PREDECESSORS':prev,'AUTH':base64.b64encode(canon(authority)).decode(),'HISTORY':base64.b64encode(history).decode()}.items():header+=k+'='+repr(v)+'\n'
body='''
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');sys.path.insert(0,str(BASE))
ROOT=Path('/var/lib/local-ai-lab');DEST=BASE.parent/'post-xe-qualification-20261106-r5';B='b60-exclusive-20261106-day-r5'
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes,load_profile
from lab_hours_exclusive_session import canonical
from lab_hours_reservations import ReservationStore
from retained_archive_integrity import load_root_owned,verify,fixed_proxmox_inventory,fixed_resolve
def call(c,timeout=30):
 p=subprocess.run(c,capture_output=True,text=True,timeout=timeout);assert p.returncode==0;return p.stdout.strip()
def create(p,data,mode=0o600):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,mode)
 with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
'''+(d/'registration_install.py.txt').read_text()+'''
with host_exclusion(ROOT):
 assert not any(p.exists() or p.is_symlink() for p in [ROOT/'lease.json',ROOT/'lease.lock',ROOT/'full-inference-drain.json',ROOT/'full-inference-drain.lock',Path('/run/local-ai-lab-operation.lock')])
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 bookings=ReservationStore(ROOT/'reservations',expected_uid=0);row=bookings.get(B)
 assert not any(v.get('state')=='claimed' for v in bookings.list())
 for peer in ('aster-news-video-xpu-20261106-1430-r1','aster-news-video-ov-20261106-1525-r1'):
  p=bookings.get(peer);assert p['state'] in {'complete','failed'} and p['finished_epoch']+900<row['start_epoch']
 scopes=call(['systemctl','list-units','--all','--no-legend','--plain','aster-local-ai-pilot-owner-*','aster-local-ai-pilot-guardian-*','b60-exclusive-owner-*','b60-exclusive-guardian-*']);assert not any(len(l.split())>3 and l.split()[2] in {'active','activating','deactivating'} for l in scopes.splitlines())
 assert row['state']=='reserved' and row['owner']=='b60-stream-a' and row['workload'] is None and row['kind']=='exclusive-stack'
 assert (row['start_epoch'],row['end_epoch'])==(1794008400,1794010200) and time.time()+120<row['start_epoch']
 assert not DEST.exists() and not (ROOT/'exclusive-sessions'/B).exists()
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')};assert len(pins)==30 and hashlib.sha256(canonical(pins)).hexdigest()=='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
 retained=load_root_owned();proof=verify(retained,fixed_proxmox_inventory(),date='2026_11_06',now_epoch=row['start_epoch']+120,resolve=fixed_resolve,lstat=os.lstat)
 history=base64.b64decode(HISTORY);assert 0<=row['start_epoch']+120-json.loads(history)['observed_epoch']<=7200
 incident=protected_bytes(ROOT/'device-incidents/b60-xe-20261106-1794002063/open.json');assert hashlib.sha256(incident).hexdigest()=='7c1355adec390764cd970036233c1a70325d224b387e751dff4ef06db0e5cc6e'
 receipt=install_registration(bookings,row)
 DEST.mkdir(mode=0o700)
 for n,data in FILES.items():create(DEST/n,base64.b64decode(data))
 create(DEST/'manifest.json',canonical(MANIFEST));sys.path.insert(0,str(DEST));from qualification import initialize;assert initialize()==MANIFEST
 guest={n:FILES[n] for n in ('fixed_command.py','known_answer_requests.py')}
 code="import os,base64,json,hashlib;from pathlib import Path;d=Path('/usr/local/libexec/local-ai-lease/post-xe-qualification-20261106-r5');assert not d.exists();d.mkdir(mode=0o755);files="+repr(guest)+";out={};\\nfor n,v in files.items():\\n raw=base64.b64decode(v);fd=os.open(d/n,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o644 if n=='fixed_command.py' else 0o600);f=os.fdopen(fd,'wb');f.write(raw);f.flush();os.fsync(f.fileno());f.close();out[n]=hashlib.sha256(raw).hexdigest()\\nprint(json.dumps(out))"
 assert json.loads(call(['pct','exec','110','--','python3','-B','-c',code]))=={n:MANIFEST[n] for n in guest}
 if (ROOT/'post-xe-authorization.json').exists():assert protected_bytes(ROOT/'post-xe-authorization.json')==base64.b64decode(AUTH)
 else:create(ROOT/'post-xe-authorization.json',base64.b64decode(AUTH))
 wrapper=base64.b64decode(FILES['guest_entry_scope.py']);guestcode="import os,base64,hashlib;from pathlib import Path;d=Path('/usr/local/libexec/local-ai-lease/post-xe-qualification-20261106-r5');assert not d.exists();d.mkdir(mode=0o700);raw=base64.b64decode("+repr(FILES['guest_entry_scope.py'])+");fd=os.open(d/'guest_entry_scope.py',os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600);f=os.fdopen(fd,'wb');f.write(raw);f.flush();os.fsync(f.fileno());f.close();print(hashlib.sha256(raw).hexdigest())"
 assert call(['pct','exec','116','--','python3','-B','-c',guestcode])==MANIFEST['guest_entry_scope.py']
 create(ROOT/'backup-chain-history'/(B+'.json'),history)
 plans={}
 for g in ('104','110','114','115','116'):
  cmd=['pct','exec',g,'--','python3','-B']+([str(DEST/'guest_entry_scope.py'),'prepare'] if g=='116' else ['/usr/local/libexec/local-ai-lease/entry-checkpoint/lab_hours_prepare_entry_plan.py'])+['--guest-id',g,'--booking-id',B]
  v=json.loads(call(cmd,60));assert v['state']=='prepared';plans[g]=v['plan_sha256']
 template=load_profile(ROOT/'exclusive-activations/b60-exclusive-20261106-day-r2.json',BASE)
 profile=dict(template,booking_id=B,guest_plans=plans,trial_seconds=600);create(ROOT/'exclusive-activations'/(B+'.json'),canonical(profile));load_profile(ROOT/'exclusive-activations'/(B+'.json'),BASE)
 cards=ROOT/'post-xe-cards';cards.mkdir(mode=0o700,exist_ok=True)
 card={'schema':'b60-post-xe-card.v1','booking_id':B,'start_epoch':row['start_epoch'],'end_epoch':row['end_epoch'],'source_sha256':MANIFEST,'incident_sha256':hashlib.sha256(incident).hexdigest(),'backup_history_sha256':hashlib.sha256(history).hexdigest(),'authorization_sha256':hashlib.sha256(base64.b64decode(AUTH)).hexdigest()}
 create(cards/(B+'.json'),canonical(card))
 sys.path.insert(0,str(BASE.parent/'full-inference-pilot'))
 from b60_post_xe_r5_card_bridge import validate_card
 assert validate_card(bookings.get(B))==hashlib.sha256(canonical(card)).hexdigest()
 name='b60-post-xe-'+B;units=Path('/etc/systemd/system')
 service='[Unit]\\nDescription=B60 exact accepted SYCL known-answer qualification\\n\\n[Service]\\nType=oneshot\\nUser=root\\nRestart=no\\nKillMode=control-group\\nTimeoutStartSec=30\\nExecStart=/usr/bin/python3 -B '+str(BASE.parent/'full-inference-pilot/lab_hours_reserved_runner.py')+' --booking-id '+B+'\\n'
 timer='[Unit]\\nDescription=B60 booked post-Xe qualification\\n\\n[Timer]\\nOnCalendar=2026-11-06 16:40:00 America/Vancouver\\nPersistent=false\\nAccuracySec=1s\\nRandomizedDelaySec=0\\nUnit='+name+'.service\\n\\n[Install]\\nWantedBy=timers.target\\n'
 for n,raw in ((name+'.service',service),(name+'.timer',timer)):create(units/n,raw.encode(),0o644)
 call(['systemd-analyze','verify',str(units/(name+'.service')),str(units/(name+'.timer'))]);call(['systemctl','daemon-reload'])
 assert subprocess.run(['systemctl','is-enabled',name+'.timer'],capture_output=True,text=True).stdout.strip()=='disabled'
 out={'schema':'b60-post-xe-inactive-integration.v1','booking_id':B,'source_sha256':MANIFEST,'registration':receipt,'guest_plan_sha256':plans,'card_sha256':hashlib.sha256(canonical(card)).hexdigest(),'profile_sha256':hashlib.sha256(canonical(profile)).hexdigest(),'timer_sha256':hashlib.sha256(timer.encode()).hexdigest(),'service_sha256':hashlib.sha256(service.encode()).hexdigest(),'archive_receipt':proof,'clock_armed':False,'model_calls':0,'installed_epoch':int(time.time())}
 p=ROOT/'integration-receipts';p.mkdir(mode=0o700,exist_ok=True);create(p/(B+'-post-xe-inactive.json'),canonical(out));print(json.dumps(out,sort_keys=True))
'''
out=Path('/private/tmp/b60-post-xe-r5-installer.py');out.write_text(header+body);compile(out.read_text(),str(out),'exec');print(hashlib.sha256(out.read_bytes()).hexdigest())
