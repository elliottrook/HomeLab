"""Fixed accepted-SYCL post-Xe qualification under the existing exclusive guardian.
No reset/driver change; one bounded candidate plus at most one entry backend start.
"""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session')
HERE=BASE.parent/'post-xe-qualification-20261106-r5'
ROOT=Path('/var/lib/local-ai-lab')
BASE_SHA='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
INCIDENT_SHA='7c1355adec390764cd970036233c1a70325d224b387e751dff4ef06db0e5cc6e'
BIN_SHA='0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
MODEL_SHA='cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13'
UNIT_SHA='a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3'
FILES={'qualification.py','fixed_command.py','known_answer_requests.py','backup_chain_history.py','guest_entry_scope.py'}
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def require(v,code):
 if v is not True:raise RuntimeError(code)
def call(args,timeout=20):
 p=subprocess.run(args,capture_output=True,text=True,timeout=timeout);require(p.returncode==0,'FIXED_COMMAND_FAILED');return p.stdout.strip()
def initialize():
 require(os.geteuid()==0 and os.uname().nodename=='proxmox','HOST_IDENTITY');sys.path.insert(0,str(BASE));sys.path.insert(0,str(HERE))
 from lab_hours_exclusive_profile import protected_bytes
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')}
 require(len(pins)==30 and hashlib.sha256(canon(pins)).hexdigest()==BASE_SHA,'BASE_SOURCE_DRIFT')
 manifest=json.loads(protected_bytes(HERE/'manifest.json'))
 require(set(manifest)==FILES and {p.name for p in HERE.glob('*.py')}==FILES,'SOURCE_CLOSURE')
 for n,sha in manifest.items():require(hashlib.sha256(protected_bytes(HERE/n,executable=True,maximum=262144)).hexdigest()==sha,'SOURCE_DRIFT')
 require(hashlib.sha256(protected_bytes(ROOT/'device-incidents/b60-xe-20261106-1794002063/open.json')).hexdigest()==INCIDENT_SHA,'INCIDENT_EVIDENCE_DRIFT')
 for b,sha in [('b60-exclusive-20261105-day-r4','b3f3c5ef5f63ea13f032c0817d510dbafc9cac62cba697b9643a0c1b30b1cd3a'),('b60-exclusive-20261105-day-r5','d6f95bd27723084c49ee620f3c54157e05b7e05e72684eb00c179c7ea72c2396')]:
  raw=protected_bytes(ROOT/'exclusive-sessions'/b/'qualification-terminal.json');require(hashlib.sha256(raw).hexdigest()==sha and json.loads(raw)['qualified'] is True,'RECOVERY_QUALIFICATION')
 return manifest

def kernel(adapter,deadline,since):
 import re
 raw=adapter._call(('journalctl','-k','--since','@'+str(int(since)),'--no-pager','-o','cat'),deadline,3)
 n=sum('out of memory' in l or 'oom-kill' in l or bool(re.search(r'\bxe\b',l)) and bool(re.search(r'\b(?:reset\w*|hang\w*|hung|wedged|device lost|fault\w*|error\w*)\b',l)) for l in raw.lower().splitlines())
 require(n==0,'NEW_DEVICE_OR_OOM_HAZARD');return {'since_epoch':int(since),'observed_epoch':int(time.time()),'new_hazards':0}

def validate_packet(v):
 require(type(v) is dict and set(v)=={'schema','state','planned_requests','attempted_requests','max_tokens','timeout_seconds','retries','records','answer_content_retained','hidden_reasoning_retained','device_recovery_qualified','requires_independent_source_bound_restoration_acceptance'} and v.get('answer_content_retained') is False and v.get('hidden_reasoning_retained') is False and v.get('device_recovery_qualified') is False and v.get('requires_independent_source_bound_restoration_acceptance') is True and v.get('schema')=='b60-post-xe-known-answer-packet.v1','PACKET_SCHEMA')
 require(v.get('planned_requests')==3 and v.get('retries')==0 and v.get('timeout_seconds')==30 and v.get('max_tokens')==128,'PACKET_CONTRACT')
 rows=v.get('records');require(type(rows) is list and 1<=len(rows)<=3 and v.get('attempted_requests')==len(rows),'PACKET_ROWS')
 for i,row in enumerate(rows):
  require(set(row)=={'request','http_status','finish_reason','answer_sha256','predicate_passed','outcome','elapsed_ms'} and row['request']==i+1,'PACKET_ROW_SCHEMA')
  require(type(row['elapsed_ms']) is int and row['elapsed_ms']>=0 and type(row['predicate_passed']) is bool,'PACKET_ROW_TYPES')
  if row['predicate_passed']:require(row['http_status']==200 and row['finish_reason']=='stop' and row['outcome']=='passed' and type(row['answer_sha256']) is str and len(row['answer_sha256'])==64 and row['elapsed_ms']<=30000,'PACKET_PASS_FIELDS')
 require(v.get('state')==('passed' if len(rows)==3 and all(x['predicate_passed'] for x in rows) else 'failed'),'PACKET_STATE');return v

def context(b):
 initialize()
 from lab_hours_exclusive_profile import protected_bytes
 from lab_hours_exclusive_cli import context as base_context
 card=json.loads(protected_bytes(ROOT/'post-xe-cards'/(b+'.json')))
 require(card['schema']=='b60-post-xe-card.v1' and card['booking_id']==b and card['source_sha256']==initialize() and card['incident_sha256']==INCIDENT_SHA,'CARD_BINDING')
 result=base_context(b);profile,store,bookings,scopes,adapter=result;row=bookings.get(b)
 require(row.get('workload')=='b60-accepted-sycl-post-xe-qualification-v2' and row.get('owner')=='b60-stream-a' and row.get('kind')=='exclusive-stack','REGISTERED_BOOKING')
 require(all(row[k]==card[k] for k in ('start_epoch','end_epoch')) and profile['trial_seconds']==600,'CARD_WINDOW')
 dispatch=json.loads(protected_bytes(ROOT/'exclusive-dispatch'/(b+'.json')))
 require(dispatch.get('card_sha256')==hashlib.sha256(protected_bytes(ROOT/'post-xe-cards'/(b+'.json'))).hexdigest(),'DISPATCH_BINDING')
 from backup_chain_history import backup
 adapter.admission.backup=lambda **kw:backup(adapter,store,card,**kw)
 prior=adapter.admission
 def admit(row,profile):
  require(not (store.root/'qualification-intent.json').exists(),'SPENT_ATTEMPT');require(prior(row,profile),'ADMISSION')
  deadline=row['end_epoch']-900
  store.write('qualification-kernel-admission.json',kernel(adapter,deadline,1794002064),immutable=True)
  from fixed_command import BINARY,MODEL
  for path,sha in [(BINARY,BIN_SHA),(MODEL,MODEL_SHA),('/etc/systemd/system/aster-llama.service',UNIT_SHA)]:require(adapter._call(('pct','exec','110','--','sha256sum',path),deadline,60).split()[0]==sha,'ACCEPTED_ARTIFACT_HASH')
  for n in ('fixed_command.py','known_answer_requests.py'):require(adapter._call(('pct','exec','110','--','sha256sum',str(HERE/n)),deadline,10).split()[0]==card['source_sha256'][n],'GUEST_SOURCE_HASH')
  available=int(adapter._call(('pct','exec','110','--','awk','/MemAvailable:/ {print $2}','/proc/meminfo'),deadline,10))*1024
  host_available=int(Path('/proc/meminfo').read_text().split('MemAvailable:')[1].split()[0])*1024
  require(available>=4*1024**3 and host_available>=24*1024**3,'MEMORY_HEADROOM')
  store.write('qualification-preflight.json',{'guest_available_bytes':available,'accepted_model_sha256':MODEL_SHA,'accepted_binary_sha256':BIN_SHA,'incident_sha256':INCIDENT_SHA,'observed_epoch':int(time.time())},immutable=True)
  return True
 adapter.admission=admit;adapter.arm=lambda state,profile:arm(b,scopes,state,store)
 original_runner=adapter.runner
 def runner(command,timeout):
  command=tuple(command)
  prefix=('pct','exec','116','--','/usr/bin/python3','-B','/usr/local/libexec/local-ai-lease/entry-checkpoint/lab_hours_guest_checkpoint.py')
  if command[:7]==prefix:
   path=str(HERE/'guest_entry_scope.py');code,raw=original_runner(('pct','exec','116','--','sha256sum',path),10)
   require(code==0 and raw.split()[0]==card['source_sha256']['guest_entry_scope.py'],'FIXED116_WRAPPER_HASH')
   command=command[:6]+(path,'checkpoint')+command[7:]

  # Both the outer adapter and its unit adapter pass the same durable latch.
  if tuple(command)==('pct','exec','110','--','systemctl','start','aster-llama.service'):
   p=store.root/'entry-backend-start-intent.json'
   if p.exists():
    code,raw=original_runner(('pct','exec','110','--','systemctl','is-active','aster-llama.service'),min(5,timeout))
    require(code==0 and raw.strip()=='active','ENTRY_BACKEND_RESTART_ALREADY_ATTEMPTED');return 0,''
   store.write(p.name,{'booking_id':b,'observed_epoch':int(time.time()),'maximum_start_attempts':1},immutable=True)
  return original_runner(command,timeout)
 adapter.runner=runner;adapter.units.runner=runner
 adapter.execute=lambda state,deadline:trial(adapter,store,state,card)
 return result

def trial(adapter,store,state,card):
 from fixed_command import start_command,UNIT
 b=state['booking_id'];unit='b60-exclusive-trial-'+b+'.service';deadline=min(state['trial_deadline'],time.time()+300)
 intent={'booking_id':b,'entry_sha256':state['entry_sha256'],'incident_sha256':INCIDENT_SHA,'source_sha256':card['source_sha256'],'observed_epoch':int(time.time()),'gpu_deadline_epoch':int(deadline),'requests':3,'reasoning':'off','candidate':'accepted9B-known-answer-qualification'}
 store.write('qualification-intent.json',intent,immutable=True)
 store.write('qualification-kernel-before.json',kernel(adapter,deadline,intent['observed_epoch']),immutable=True)
 cmd=list(start_command());cmd[cmd.index('--unit='+UNIT)]='--unit='+unit;cmd[cmd.index('--property=Type=simple')]='--property=Type=exec'
 i=cmd.index('--setenv=LD_LIBRARY_PATH='+__import__('fixed_command').LD_LIBRARY_PATH)
 cmd[i:i]=['--property=MemoryMax=14G','--property=MemorySwapMax=0','--property=CPUQuota=400%','--property=TasksMax=256','--property=KillMode=control-group','--property=RuntimeMaxSec=300','--property=StandardOutput=null','--property=StandardError=journal']
 adapter._call(cmd,deadline,20)
 until=min(deadline-100,time.time()+120)
 while time.time()<until:
  kernel(adapter,deadline,intent['observed_epoch'])
  code,raw=adapter.runner(('pct','exec','110','--','curl','-fsS','--max-time','3','http://192.168.70.12:11435/health'),5)
  if code==0:break
  fields=adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=ActiveState'),deadline,5);require('ActiveState=failed' not in fields,'CANDIDATE_FAILED');time.sleep(2)
 else:raise RuntimeError('CANDIDATE_READY_DEADLINE')
 limits=dict(x.split('=',1) for x in adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=MemoryMax,MemorySwapMax,TasksMax,CPUQuotaPerSecUSec,RuntimeMaxUSec,KillMode,Restart'),deadline,5).splitlines())
 require(limits.get('MemoryMax')==str(14*1024**3) and limits.get('MemorySwapMax')=='0' and limits.get('TasksMax')=='256' and limits.get('CPUQuotaPerSecUSec')=='4s' and limits.get('RuntimeMaxUSec')=='5min' and limits.get('KillMode')=='control-group' and limits.get('Restart')=='no','CANDIDATE_LIMITS')
 store.write('qualification-effective-limits.json',limits,immutable=True)
 # Sanitize residency in the source guest; never return argv or raw logs.
 code="import json;from pathlib import Path;import sys;p=sys.argv[1];v=[];\nfor f in (Path('/proc')/p/'fdinfo').glob('*'):\n t=f.read_text();d={k.strip():x.strip() for k,s,x in (l.partition(':') for l in t.splitlines()) if s};\n if d.get('drm-driver')=='xe':v.append(d)\nprint(json.dumps({'xe_fd_count':len(v),'vram_field_present':any('drm-resident-vram0' in d for d in v),'gtt_field_present':any('drm-resident-gtt' in d for d in v),'vram_resident_kib':max([int(d.get('drm-resident-vram0','0 KiB').split()[0]) for d in v] or [0]),'gtt_resident_kib':max([int(d.get('drm-resident-gtt','0 KiB').split()[0]) for d in v] or [0])}))"
 pid=adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=MainPID','--value'),deadline,10).strip();require(pid.isdigit() and int(pid)>0,'CANDIDATE_PID')
 resident=json.loads(adapter._call(('pct','exec','110','--','python3','-B','-c',code,pid),deadline,10))
 require(resident['xe_fd_count']>0 and resident['vram_field_present'] and resident['gtt_field_present'] and 4*1024**2<=resident['vram_resident_kib']<=14*1024**2 and resident['gtt_resident_kib']<=2*1024**2,'GPU_RESIDENCY_UNPROVEN')

 store.write('qualification-residency.json',resident,immutable=True)
 logs=adapter._call(('pct','exec','110','--','journalctl','-u',unit,'--no-pager','-o','cat','-n','400'),deadline,5)
 import re
 layers=re.findall(r'offloaded (\d+)/(\d+) layers',logs)
 require(bool(layers) and int(layers[-1][0])==int(layers[-1][1])>0 and 'sycl' in logs.lower(),'GPU_OFFLOAD_UNPROVEN')
 store.write('qualification-offload.json',{'all_layers_offloaded':True,'layers':int(layers[-1][0]),'engine':'SYCL'},immutable=True)

 require(time.time()+95<deadline,'REQUEST_MARGIN')
 raw=adapter._call(('pct','exec','110','--','python3','-B',str(HERE/'known_answer_requests.py'),'--run-authorized'),deadline,95)
 require(len(raw.encode())<=8192,'PACKET_SIZE');packet=validate_packet(json.loads(raw));store.write('qualification-answers.json',packet,immutable=True)
 store.write('qualification-kernel-after.json',kernel(adapter,deadline,intent['observed_epoch']),immutable=True)
 require(packet['state']=='passed','KNOWN_ANSWER_FAILED');return True

def arm(b,scopes,state,store):
 remaining=int(state['restore_deadline']-time.time());require(remaining>900,'GUARDIAN_MARGIN')
 call(['systemd-run','--quiet','--unit='+scopes.guardian,'--property=Type=exec','--property=KillMode=control-group','--property=Restart=no','--property=TimeoutStopSec=30','--property=RuntimeMaxSec='+str(remaining+600),'/usr/bin/python3','-B',str(HERE/'qualification.py'),'watch','--booking-id',b],15)
 fields=dict(l.split('=',1) for l in call(['systemctl','show',scopes.guardian,'--property=ActiveState,MainPID,KillMode,Restart']).splitlines())
 ok=fields.get('ActiveState')=='active' and int(fields.get('MainPID','0'))>0 and fields.get('KillMode')=='control-group' and fields.get('Restart')=='no'
 if ok:store.write('model-guardian.json',{'independent_guardian_armed':True,'observed_epoch':int(time.time())},immutable=True)
 return ok


def operate(action,b):
 profile,store,bookings,scopes,adapter=context(b)
 from lab_hours_exclusive_session import ExclusiveSession
 from lab_hours_exclusive_guardian import guard
 try:
  if action=='launch':
   row=bookings.get(b);now=int(time.time());require(row['state']=='reserved' and row['start_epoch']<=now<=row['start_epoch']+120,'LAUNCH_WINDOW')
   call(['systemd-run','--quiet','--unit='+scopes.owner,'--property=Type=exec','--property=KillMode=control-group','--property=Restart=no','--property=TimeoutStopSec=30','--property=RuntimeMaxSec='+str(row['end_epoch']-now+300),'/usr/bin/python3','-B',str(HERE/'qualification.py'),'run','--booking-id',b],15)
   return {'state':'owner-launched','booking_id':b}
  if action=='watch':
   def alive(state):
    p=store.root/'qualification-intent.json'
    if p.exists() and state['phase'] not in {'restoring','restored','released','released-late'}:
     try:
      intent=store.read(p.name);require(time.time()<intent['gpu_deadline_epoch'],'GPU_EXPOSURE_DEADLINE');kernel(adapter,time.time()+4,intent['observed_epoch'])
     except Exception:
      store.write('qualification-guardian-stop.json',{'new_fault_or_monitor_failure':True,'observed_epoch':int(time.time())});return False
    return scopes.alive(state)
   return guard(store,adapter,owner=profile['owner'],owner_alive=alive,fence_owner=scopes.fence)
  require(action=='run' and scopes._show().get('MainPID')==str(os.getpid()) and scopes.alive({}),'OWNER_SCOPE')
  session=ExclusiveSession(store,adapter)
  try:
   session.begin(bookings.get(b),owner=profile['owner'],trial_seconds=600)
   result=session.run_trial(owner=profile['owner'])
   packet=store.read('qualification-answers.json') if (store.root/'qualification-answers.json').exists() else None
   passed=result.get('outcome')=='complete-restored' and packet is not None and packet['state']=='passed'
   store.write('post-xe-terminal.json',{'schema':'b60-post-xe-terminal.v1','booking_id':b,'qualified':passed,'session_outcome':result.get('outcome'),'answers_sha256':hashlib.sha256(canon(packet)).hexdigest() if packet else None,'source_sha256':initialize(),'incident_sha256':INCIDENT_SHA,'finished_epoch':int(time.time()),'requires_independent_restoration_acceptance':True},immutable=True)
   return result
  except BaseException as error:
   store.write('qualification-owner-failure.json',{'failure_type':type(error).__name__,'observed_epoch':int(time.time())})
   # Never retry recovery/start here: run_trial already invokes recovery. The
   # armed independent guardian owns rescue if the owner exits while unfinished.
   raise
 finally:adapter.boundary.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=('launch','run','watch'));p.add_argument('--booking-id',required=True);a=p.parse_args()
 try:initialize();print(json.dumps(operate(a.action,a.booking_id),sort_keys=True))
 except Exception as e:print(json.dumps({'state':'no_go','failure_type':type(e).__name__}));raise SystemExit(1)
