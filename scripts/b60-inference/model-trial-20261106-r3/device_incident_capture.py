"""Record the actual shared-device incident; no raw logs or GPU operation."""
import hashlib,json,os,re,stat,subprocess,sys,time
from pathlib import Path
ROOT=Path('/var/lib/local-ai-lab');BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session');ID='b60-xe-20261106-1794002063';PEER='aster-news-video-xpu-20261106-1430-r1'
def call(a,timeout=20):
 p=subprocess.run(a,capture_output=True,text=True,timeout=timeout);assert p.returncode==0;return p.stdout.strip()
def create(p,raw):
 fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 fd=os.open(p.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
assert os.geteuid()==0 and os.uname().nodename=='proxmox'
sys.path.insert(0,str(BASE))
from host_exclusion import host_exclusion
from lab_hours_exclusive_profile import protected_bytes
from lab_hours_exclusive_session import canonical
with host_exclusion(ROOT):
 assert not any((ROOT/n).exists() or (ROOT/n).is_symlink() for n in ('lease.json','lease.lock','full-inference-drain.json','full-inference-drain.lock')) and not Path('/run/local-ai-lab-operation.lock').exists()
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')};assert len(pins)==30 and hashlib.sha256(canonical(pins)).hexdigest()=='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
 booking_raw=protected_bytes(ROOT/'reservations/records'/(PEER+'.json'));peer=json.loads(booking_raw);assert peer['state']=='failed' and peer['finished_epoch']==1794002208 and peer['current_attempt']==2
 units=call(['systemctl','list-units','--all','--plain','--no-legend','*lh-f3d088baff35aee50457*'])
 assert not any(len(l.split())>3 and l.split()[2] in ('active','activating','deactivating') for l in units.splitlines())
 terminal_path=ROOT/'lab-hours-attempts'/('reservation-'+PEER+'-attempt-2')/'terminal.json';terminal_raw=protected_bytes(terminal_path);terminal=json.loads(terminal_raw);assert terminal['production_restored'] is True
 raw=call(['journalctl','-k','--since','@1794000600','--no-pager','-o','json']);events=[]
 for line in raw.splitlines():
  v=json.loads(line);m=v.get('MESSAGE','').lower();kinds=[]
  if re.search(r'\bxe\b',m):
   if re.search(r'\breset\w*\b',m):kinds.append('xe_engine_reset')
   if re.search(r'\bfault\w*\b',m):kinds.append('xe_fault')
  if kinds:events.append({'epoch_microseconds':int(v['__REALTIME_TIMESTAMP']),'categories':kinds,'priority':v.get('PRIORITY')})
 assert len(events)==3 and events[0]['epoch_microseconds']==1794002063552040
 from full_inference_lab_runtime import _gpu_users
 users=_gpu_users();holder_ok=len(users)==1 and next(iter(users)).cgroup.endswith('/lxc/110/ns/system.slice/aster-llama.service')
 assert holder_ok
 call(['pct','exec','110','--','/usr/local/sbin/aster-llama-production-auth-probe'])
 # Source-reviewed probe is GET/v1/models only. Its exit0 is service restoration,
 # never a model generation or a known-answer post-reset correctness pass.
 binary=call(['pct','exec','110','--','sha256sum','/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server']).split()[0]
 unit=call(['pct','exec','110','--','sha256sum','/etc/systemd/system/aster-llama.service']).split()[0]
 assert binary=='0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5' and unit=='a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3'
 value={'schema':'b60-shared-device-incident.v1','incident_id':ID,'state':'OPEN','observed_epoch':int(time.time()),'source':'proxmox-kernel-journal','producer_sha256':PRODUCER_SHA256,'peer_booking_id':PEER,'peer_booking_sha256':hashlib.sha256(booking_raw).hexdigest(),'peer_terminal_sha256':hashlib.sha256(terminal_raw).hexdigest(),'peer_attempt':2,'peer_finished_epoch':peer['finished_epoch'],'peer_production_restored':True,'events':events,'journal_sha256':hashlib.sha256(raw.encode()).hexdigest(),'raw_logs_exported':False,'accepted_gpu_holder_only':True,'accepted_binary_sha256':binary,'accepted_unit_sha256':unit,'metadata_only_auth_probe_exit':0,'post_reset_known_answer_qualification_present':False,'new_model_calls':0,'device_resets_requested':0,'driver_or_service_changes':False,'gate':'no-B60-experiment-dispatch-until-source-bound-incident-closure'}
 parent=ROOT/'device-incidents';parent.mkdir(mode=0o700,exist_ok=True)
 s=parent.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==0 and stat.S_IMODE(s.st_mode)==0o700
 dest=parent/ID;assert not dest.exists();dest.mkdir(mode=0o700);payload=canonical(value);create(dest/'open.json',payload)
 print(json.dumps({'incident':value,'path':str(dest/'open.json'),'sha256':hashlib.sha256(payload).hexdigest()},sort_keys=True))
