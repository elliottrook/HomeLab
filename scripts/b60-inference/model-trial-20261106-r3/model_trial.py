"""Fixed 35B compatibility trial using the qualified entry/guardian controller.

A separate exact protected card and full source closure authorize only this
candidate; the unchanged base activation remains no-model. No ledger command,
external model code, guessed admission or unrestricted recovery is accepted.
"""
import argparse,hashlib,json,os,stat,subprocess,sys,time
from pathlib import Path
BASE=Path('/usr/local/libexec/local-ai-lease/exclusive-session')
HERE=Path('/usr/local/libexec/local-ai-lease/model-trial-20261106-r3')
ROOT=Path('/var/lib/local-ai-lab')
BASE_SHA='e282a0e6a26a7e0302a70d2dbf953734048a5eb3697704d3cf0dce48803c3cd2'
MODEL_ROOT=Path('/var/lib/vz/aster-model-staging/qwen36-35b-a3b-v1')
MODEL=MODEL_ROOT/'Qwen3.6-35B-A3B-Q4_K_M.gguf'
MODEL_SHA='671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7'
MODEL_BYTES=20419565568
TARGET='/opt/models/aster-first-screen'
GUEST_REQUEST='/usr/local/libexec/local-ai-lease/model-trial-20261106-r3/guest_requests.py'
BIN_SHA='0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
UNIT_SHA='a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3'


def require(v,code):
 if v is not True:raise RuntimeError(code)
def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def call(a,timeout=20):
 p=subprocess.run(a,capture_output=True,text=True,timeout=timeout)
 require(p.returncode==0,'FIXED_COMMAND_FAILED');return p.stdout.strip()

def initialize():
 require(os.geteuid()==0 and os.uname().nodename=='proxmox','HOST_IDENTITY')
 sys.path.insert(0,str(BASE))
 from lab_hours_exclusive_profile import protected_bytes
 pins={p.name:hashlib.sha256(protected_bytes(p,executable=True,maximum=262144)).hexdigest() for p in BASE.glob('*.py')}
 require(len(pins)==30 and hashlib.sha256(canon(pins)).hexdigest()==BASE_SHA,'BASE_SOURCE_DRIFT')
 manifest=json.loads(protected_bytes(HERE/'manifest.json'))
 require(set(manifest)=={'model_trial.py','namespace_mount.py','fixed_command.py','guest_requests.py','guest_supervisor.py','backup_chain_history.py','legacy_requests.py','request_failure_capture.py','news_xpu_boundary.py','guest_entry_scope.py'},'SOURCE_CLOSURE')
 require(set(p.name for p in HERE.glob('*.py'))==set(manifest),'SOURCE_CLOSURE')
 for name,sha in manifest.items():require(hashlib.sha256(protected_bytes(HERE/name,executable=True,maximum=262144)).hexdigest()==sha,'SOURCE_DRIFT')
 for booking,sha in [('b60-exclusive-20261105-day-r4','b3f3c5ef5f63ea13f032c0817d510dbafc9cac62cba697b9643a0c1b30b1cd3a'),('b60-exclusive-20261105-day-r5','d6f95bd27723084c49ee620f3c54157e05b7e05e72684eb00c179c7ea72c2396')]:
  proof=protected_bytes(ROOT/'exclusive-sessions'/booking/'qualification-terminal.json')
  require(hashlib.sha256(proof).hexdigest()==sha and json.loads(proof).get('qualified') is True,'EXACT_RECOVERY_QUALIFICATION_REQUIRED')
 return manifest

def card_for(booking_id):
 from lab_hours_exclusive_profile import protected_bytes
 from lab_hours_exclusive_session import IDENTITY
 require(isinstance(booking_id,str) and IDENTITY.fullmatch(booking_id) is not None,'BOOKING_IDENTITY')
 card=json.loads(protected_bytes(ROOT/'model-trial-cards'/(booking_id+'.json')))
 require(set(card)=={'schema','booking_id','start_epoch','end_epoch','source_sha256','candidate_sha256','base_source_map_sha256','mode','backup_history_sha256'},'CARD_SCHEMA')
 require(card['schema']=='b60-fixed-model-trial.v1' and card['booking_id']==booking_id and card['mode']=='qwen36-35b-reasoning-compatibility-v1' and card['candidate_sha256']==MODEL_SHA and card['base_source_map_sha256']==BASE_SHA,'CARD_IDENTITY')
 require(card['source_sha256']==initialize(),'CARD_SOURCE_DRIFT')
 return card

def context(b):
 card=card_for(b)
 from lab_hours_exclusive_cli import context as base_context
 result=base_context(b);profile,store,bookings,scopes,adapter=result
 row=bookings.get(b)
 require(row.get('workload')=='b60-qwen36-35b-failure-capture-v1','REGISTERED_WORKLOAD_REQUIRED')
 from lab_hours_exclusive_profile import protected_bytes
 dispatch=json.loads(protected_bytes(ROOT/'exclusive-dispatch'/(b+'.json')))
 expected={k:row[k] for k in ('booking_id','owner','kind','workload','start_epoch','end_epoch')}
 require(dispatch.get('schema')=='b60-registered-exclusive-dispatch.v1' and dispatch.get('booking_identity')==expected and dispatch.get('card_sha256')==hashlib.sha256(protected_bytes(ROOT/'model-trial-cards'/(b+'.json'))).hexdigest() and dispatch.get('claimant')=='qualified-inner-owner-only','REGISTERED_DISPATCH_REQUIRED')
 require(row.get('owner')=='b60-stream-a' and row.get('kind')=='exclusive-stack' and all(row[k]==card[k] for k in ('booking_id','start_epoch','end_epoch')),'BOOKING_CARD_DRIFT')
 require(profile['experiment'] is None and profile['qualification_only'] is True and profile['trial_seconds']==1200,'BASE_ACTIVATION_DRIFT')
 from backup_chain_history import backup
 adapter.admission.backup=lambda **kwargs:backup(adapter,store,card,**kwargs)
 original_admit=adapter.admission
 def admission(row,profile):
  require(not (store.root/'model-intent.json').exists(),'SPENT_MODEL_ATTEMPT')
  require(original_admit(row,profile),'BASE_ADMISSION')
  from news_xpu_boundary import observe
  observe(adapter,store,row)
  preflight(adapter,store,row)
  return True
 adapter.admission=admission
 adapter.arm=lambda state,profile:arm(b,scopes,state,store)
 original_restore=adapter.restore
 def restore(entry,deadline):
  cleanup(adapter,store,deadline)
  return original_restore(entry,deadline)
 adapter.restore=restore
 def execute(state,deadline):
  try:return trial(adapter,store,state)
  except Exception as error:
   store.write('model-failure.json',{'failure_type':type(error).__name__,'failure_code':str(error) if type(error) is RuntimeError and str(error).replace('_','').isalnum() else 'UNCLASSIFIED','observed_epoch':int(time.time())},immutable=True)
   raise
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
 original_fence=adapter.fence_experiments
 def fence(state):
  deadline=max(state['restore_deadline'],time.time()+300)
  unit='b60-exclusive-client-'+state['booking_id']+'.service'
  adapter.runner(('pct','exec','110','--','systemctl','stop',unit),min(30,deadline-time.time()))
  code,raw=adapter.runner(('pct','exec','110','--','systemctl','show',unit,'--property=LoadState,MainPID,TasksCurrent'),min(10,deadline-time.time()))
  require(len(raw)<=4096,'CLIENT_SCOPE_OBSERVATION')
  fields=dict(l.split('=',1) for l in raw.splitlines() if '=' in l)
  absent=code in {0,1} and fields.get('LoadState')=='not-found'
  empty=code==0 and fields.get('MainPID')=='0' and fields.get('TasksCurrent') in {'','0','[not set]'}
  require(absent or empty,'CLIENT_SCOPE_NOT_FENCED')
  return original_fence(state)
 adapter.fence_experiments=fence
 adapter.execute=execute
 return result

def target_observation(adapter,deadline):
 code="import json,os,stat;from pathlib import Path;p=Path('/opt/models/aster-first-screen');rows=[l.split() for l in Path('/proc/self/mountinfo').read_text().splitlines() if l.split()[4]==str(p)];out={'exists':p.exists(),'symlink':p.is_symlink(),'mounts':len(rows)};\nif p.exists():\n s=p.lstat();out.update(dev=s.st_dev,ino=s.st_ino,uid=s.st_uid,gid=s.st_gid,mode=stat.S_IMODE(s.st_mode),directory=stat.S_ISDIR(s.st_mode),readonly=bool(os.statvfs(p).f_flag&os.ST_RDONLY));out['empty']=not any(p.iterdir()) if not rows else False\nif rows:out['mount_id']=rows[0][0];out['mount_options']=rows[0][5]\nprint(json.dumps(out))"
 return json.loads(adapter._call(('pct','exec','110','--','python3','-B','-c',code),deadline,10))

def source_metadata():
 out={}
 for name,p in [('root',MODEL_ROOT),('model',MODEL)]:
  s=p.lstat();require(not p.is_symlink() and s.st_nlink==(2 if name=='root' else 1),'SOURCE_CUSTODY')
  require((stat.S_ISDIR(s.st_mode) if name=='root' else stat.S_ISREG(s.st_mode)),'SOURCE_TYPE')
  out[name]={'dev':s.st_dev,'ino':s.st_ino,'uid':s.st_uid,'gid':s.st_gid,'mode':stat.S_IMODE(s.st_mode),'bytes':s.st_size}
 require(out['model']['bytes']==MODEL_BYTES,'MODEL_SIZE')
 return out

def kernel_check(adapter,deadline,since):
 raw=adapter._call(('journalctl','-k','--since','@'+str(int(since)),'--no-pager','-o','cat'),deadline,3)
 from news_xpu_boundary import hazards
 bad=hazards(raw)
 require(not bad,'KERNEL_DEVICE_OR_OOM_HAZARD')
 return {'new_kernel_hazard_count':0,'since_epoch':int(since),'observed_epoch':int(time.time())}

def preflight(adapter,store,row):
 deadline=row['end_epoch']-900
 store.write('model-kernel-before.json',kernel_check(adapter,deadline,time.time()-600),immutable=True)
 metadata=source_metadata()
 require(all(v['uid']==0 and v['gid']==0 for v in metadata.values()) and metadata['root']['mode']==0o700 and metadata['model']['mode']==0o400,'ROOT_CUSTODY')
 require(digest(MODEL)==MODEL_SHA and source_metadata()==metadata,'STAGED_MODEL_HASH')
 # Pin every guest executable before the protected source is admitted.
 manifest=initialize()
 for name in ('guest_requests.py','guest_supervisor.py','fixed_command.py','legacy_requests.py','request_failure_capture.py'):
  require(adapter._call(('pct','exec','110','--','sha256sum',str(Path(GUEST_REQUEST).parent/name)),deadline,10).split()[0]==manifest[name],'GUEST_WORKLOAD_SOURCE')
 from fixed_command import BINARY
 require(adapter._call(('pct','exec','110','--','sha256sum',BINARY),deadline,30).split()[0]==BIN_SHA,'RUNTIME_HASH')
 require(adapter._call(('pct','exec','110','--','sha256sum','/etc/systemd/system/aster-llama.service'),deadline,10).split()[0]==UNIT_SHA,'ACCEPTED_UNIT_HASH')
 guest_memory=int(adapter._call(('pct','exec','110','--','awk','/MemAvailable:/ {print $2}','/proc/meminfo'),deadline,10))*1024
 disk=int(adapter._call(('pct','exec','110','--','df','--output=avail','-B1','/opt/models'),deadline,10).split()[-1])
 host_memory=int(Path('/proc/meminfo').read_text().split('MemAvailable:')[1].split()[0])*1024
 require(guest_memory>=4*1024**3 and disk>=5*1024**3 and host_memory>=24*1024**3,'RESOURCE_HEADROOM')
 observed=target_observation(adapter,deadline)
 require(observed['mounts']==0 and not observed['symlink'] and (not observed['exists'] or observed['directory'] and observed['empty']),'TARGET_NOT_FREE')
 # No persistent Proxmox mount changes are permitted in this implementation.
 raw=adapter._call(('pct','config','110','--current'),deadline,10)
 require(not any('mp='+TARGET in line for line in raw.splitlines()),'PERSISTENT_TARGET_MOUNT_PRESENT')
 store.write('model-preflight.json',{'model_sha256':MODEL_SHA,'model_bytes':MODEL_BYTES,'source':metadata,'target_entry':observed,'guest_memory_available':guest_memory,'guest_disk_available':disk,'host_memory_available':host_memory,'observed_epoch':int(time.time()),'license':'Apache-2.0','upstream_revision':'995ad96eacd98c81ed38be0c5b274b04031597b0','gguf_revision':'baec3ebee244827cda0f4557eafa8b28f7545fa6'},immutable=True)

def candidate_host_pid(adapter,unit,deadline):
 guest_pid=adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=MainPID','--value'),deadline,10).strip()
 require(guest_pid.isdigit() and int(guest_pid)>1,'CANDIDATE_GUEST_PID')
 found=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   fields=dict(l.split(':',1) for l in (p/'status').read_text().splitlines() if ':' in l)
   if fields.get('NSpid','').split()[-1:]!=[guest_pid]:continue
   if (p/'cgroup').read_text().strip().endswith('/lxc/110/ns/system.slice/'+unit):found.append(int(p.name))
  except (FileNotFoundError,ProcessLookupError):pass
 require(len(found)==1,'CANDIDATE_HOST_PID_AMBIGUOUS')
 return found[0]

def namespace_action(adapter,store,deadline,unit):
 pid=candidate_host_pid(adapter,unit,deadline)
 init_pid=int(adapter._call(('lxc-info','-n','110','-pH'),deadline,10))
 for _ in range(50):
  if os.readlink('/proc/'+str(pid)+'/ns/mnt')!=os.readlink('/proc/'+str(init_pid)+'/ns/mnt'):break
  time.sleep(.1)
 else:raise RuntimeError('CANDIDATE_NAMESPACE_NOT_PRIVATE')
 source=store.read('model-preflight.json')['source']['root']
 code=('import sys;sys.path.insert(0,'+repr(str(HERE))+');from namespace_mount import transfer;transfer('+repr(str(MODEL_ROOT))+','+repr(TARGET)+','+str(pid)+',production_pid='+str(init_pid)+')')
 store.write('model-namespace-intent.json',{'booking_id':store.read('session.json')['booking_id'],'candidate_host_pid':pid,'private_namespace':os.readlink('/proc/'+str(pid)+'/ns/mnt'),'guest_init_namespace':os.readlink('/proc/'+str(init_pid)+'/ns/mnt'),'source_dev':source['dev'],'source_ino':source['ino']},immutable=True)
 adapter._call(('/usr/bin/python3','-B','-c',code),deadline,20)
 # Read only from the candidate root, not the guest's production namespace.
 target=Path('/proc')/str(pid)/'root'/TARGET.lstrip('/')
 observed=target.stat()
 require((observed.st_dev,observed.st_ino)==(source['dev'],source['ino']) and bool(os.statvfs(target).f_flag&os.ST_RDONLY),'PRIVATE_MAPPING_UNVERIFIED')
 return pid

def exact_target(observed,source):
 return (observed.get('mounts')==1 and observed.get('dev')==source['dev'] and observed.get('ino')==source['ino'] and observed.get('readonly') is True and not observed.get('symlink'))

def cleanup(adapter,store,deadline):
 if not (store.root/'model-intent.json').exists():return
 intent=store.read('model-intent.json');state=store.read('session.json')
 require(intent['booking_id']==state['booking_id'] and intent['entry_sha256']==state['entry_sha256'] and intent['model_sha256']==MODEL_SHA,'RECOVERY_BINDING')
 # Session.recover has already fenced the exact trial scope and all consumers.
 original=store.read('model-preflight.json');source=source_metadata()
 require(all(source[n][k]==original['source'][n][k] for n in source for k in ('dev','ino','bytes')),'RECOVERY_SOURCE_IDENTITY')
 for name,v in source.items():
  require((v['uid'],v['gid'],v['mode']) in {(0,0,0o700 if name=='root' else 0o400),(100999,100991,0o700 if name=='root' else 0o400)},'RECOVERY_CUSTODY_UNKNOWN')
 # The exact candidate cgroup was fenced by base recovery first. Its mount
 # namespace must have no remaining process; production namespace never owned
 # this mount. No persistent or lazy unmount is attempted.
 if (store.root/'model-namespace-intent.json').exists():
  intent_ns=store.read('model-namespace-intent.json')
  for p in Path('/proc').glob('[0-9]*'):
   try: require(os.readlink(p/'ns/mnt')!=intent_ns['private_namespace'],'CANDIDATE_NAMESPACE_STILL_LIVE')
   except (FileNotFoundError,ProcessLookupError):pass
 observed=target_observation(adapter,deadline)
 require(observed['mounts']==0,'PRODUCTION_TARGET_MOUNT_PRESENT')
 if not original['target_entry']['exists'] and observed['exists']:
  require(observed['directory'] and observed['empty'] and not observed['symlink'],'TARGET_DIRECTORY_DRIFT')
  adapter._call(('pct','exec','110','--','rmdir',TARGET),deadline,10)
 elif original['target_entry']['exists']:
  require(all(observed.get(k)==original['target_entry'].get(k) for k in ('dev','ino','uid','gid','mode','empty','directory')),'TARGET_ENTRY_DRIFT')
 store.write('model-cleanup.json',{'phase':'custody-intent','binding':intent})
 for p in (MODEL,MODEL_ROOT):os.chown(p,0,0,follow_symlinks=False)
 require(source_metadata()==original['source'],'ROOT_CUSTODY_RESTORE')
 store.write('model-cleanup.json',{'phase':'verified','binding':intent,'mount_absent':True,'custody_restored':True,'target_entry_restored':True})

def trial(adapter,store,state):
 deadline=state['trial_deadline'];b=state['booking_id'];unit='b60-exclusive-trial-'+b+'.service'
 pre=store.read('model-preflight.json')
 require(source_metadata()==pre['source'],'PRE_EFFECT_SOURCE_DRIFT')
 require(target_observation(adapter,deadline)==pre['target_entry'],'PRE_EFFECT_TARGET_DRIFT')
 store.write('model-intent.json',{'booking_id':b,'entry_sha256':state['entry_sha256'],'model_sha256':MODEL_SHA,'observed_epoch':int(time.time())},immutable=True)
 if not pre['target_entry']['exists']:
  adapter._call(('pct','exec','110','--','install','-d','-m','0700',TARGET),deadline,10)
 # Parent custody remains root-private on the host; only these two exact inodes
 # gain mapped ollama custody, then the namespace mount is strictly read-only.
 os.chown(MODEL_ROOT,100999,100991,follow_symlinks=False);os.chown(MODEL,100999,100991,follow_symlinks=False)
 from fixed_command import start_command,UNIT,BINARY
 command=list(start_command());command[command.index('--property=Type=simple')]='--property=Type=exec';command[command.index('--unit='+UNIT)]='--unit='+unit
 at=command.index(BINARY);command[at:]=['/usr/bin/python3','-B',str(Path(GUEST_REQUEST).parent/'guest_supervisor.py'),'--deadline',str(int(deadline))];command[at:at]=['--property=PrivateMounts=yes','--property=KillMode=control-group','--property=RuntimeMaxSec='+str(max(1,int(deadline-time.time()))),'--property=MemoryMax=14G','--property=MemorySwapMax=0','--property=CPUQuota=400%','--property=TasksMax=256','--property=StandardOutput=null','--property=StandardError=journal']
 store.write('model-start-intent.json',{'booking_id':b,'unit':unit,'model_sha256':MODEL_SHA,'reasoning_enabled':True,'speculation':False,'requests':2,'request_timeout_seconds':60,'retries':0},immutable=True)
 adapter._call(command,deadline,20)
 for _ in range(30):
  main=adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=MainPID','--value'),deadline,10).strip()
  if main.isdigit() and int(main)>1:break
  time.sleep(.2)
 else:raise RuntimeError('SUPERVISOR_NOT_STARTED')
 namespace_action(adapter,store,deadline,unit)
 ready_until=min(deadline-150,time.time()+330)
 while time.time()<ready_until:
  code,raw=adapter.runner(('pct','exec','110','--','curl','-fsS','--max-time','3','http://192.168.70.12:11435/health'),5)
  if code==0:break
  kernel_check(adapter,deadline,pre['observed_epoch'])
  # A failed unit is never retried or restarted.
  fields=adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=ActiveState,MainPID'),deadline,10)
  require('ActiveState=failed' not in fields,'MODEL_UNIT_FAILED')
  time.sleep(2)
 else:raise RuntimeError('MODEL_HEALTH_DEADLINE')
 require(time.time()+130<deadline,'REQUEST_MARGIN')
 # Sanitize residency in the source guest; never return argv or raw logs.
 code="import json;from pathlib import Path;import sys;p=sys.argv[1];v=[];\nfor f in (Path('/proc')/p/'fdinfo').glob('*'):\n t=f.read_text();d={k.strip():x.strip() for k,s,x in (l.partition(':') for l in t.splitlines()) if s};\n if d.get('drm-driver')=='xe':v.append(d)\nprint(json.dumps({'xe_fd_count':len(v),'vram_field_present':any('drm-resident-vram0' in d for d in v),'gtt_field_present':any('drm-resident-gtt' in d for d in v),'vram_resident_kib':max([int(d.get('drm-resident-vram0','0 KiB').split()[0]) for d in v] or [0]),'gtt_resident_kib':max([int(d.get('drm-resident-gtt','0 KiB').split()[0]) for d in v] or [0])}))"
 pid=adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=MainPID','--value'),deadline,10).strip();require(pid.isdigit() and int(pid)>0,'CANDIDATE_PID')
 resident=json.loads(adapter._call(('pct','exec','110','--','python3','-B','-c',code,pid),deadline,10))
 require(resident['xe_fd_count']>0 and resident['vram_field_present'] and resident['gtt_field_present'] and 16*1024**2<=resident['vram_resident_kib']<=24*1024**2 and resident['gtt_resident_kib']<=2*1024**2,'GPU_RESIDENCY_UNPROVEN')
 rss=adapter._call(('pct','exec','110','--','ps','-o','rss=','-p',pid),deadline,10).strip()
 require(rss.isdigit() and int(rss)<=16*1024**2,'MODEL_RSS_LIMIT')
 resident['process_rss_kib']=int(rss)
 limits=dict(l.split('=',1) for l in adapter._call(('pct','exec','110','--','systemctl','show',unit,'--property=MemoryCurrent,MemoryPeak,MemoryMax,TasksCurrent,TasksMax,CPUQuotaPerSecUSec'),deadline,10).splitlines())
 require(limits.get('MemoryMax')==str(14*1024**3) and limits.get('TasksMax')=='256' and limits.get('CPUQuotaPerSecUSec')=='4s','MODEL_CGROUP_LIMIT_DRIFT')
 resident['cgroup']=limits
 logs=adapter._call(('pct','exec','110','--','journalctl','-u',unit,'--no-pager','-o','cat','-n','800'),deadline,10)
 import re
 layers=re.findall(r'offloaded (\d+)/(\d+) layers',logs)
 require(bool(layers) and int(layers[-1][0])==int(layers[-1][1])>0 and ('sycl' in logs.lower()),'FULL_GPU_OFFLOAD_UNPROVEN')
 resident['all_layers_offloaded']=True;resident['offloaded_layers']=int(layers[-1][0]);resident['reasoning_mode_flag']='on'
 store.write('model-residency.json',resident,immutable=True)
 client='b60-exclusive-client-'+b+'.service'
 store.write('model-client-intent.json',{'booking_id':b,'unit':client,'memory_max_bytes':128*1024**2,'runtime_seconds':130,'observed_epoch':int(time.time())},immutable=True)
 raw=adapter._call(('pct','exec','110','--','systemd-run','--quiet','--wait','--pipe','--collect','--unit='+client,'--property=Type=exec','--property=Restart=no','--property=KillMode=control-group','--property=MemoryMax=128M','--property=MemorySwapMax=0','--property=CPUQuota=25%','--property=TasksMax=16','--property=RuntimeMaxSec=130','--property=TimeoutStopSec=5','python3','-B',GUEST_REQUEST,'--run-authorized'),deadline,130)
 result=retain_request_packet(raw,store)
 store.write('model-kernel-after.json',kernel_check(adapter,deadline,pre['observed_epoch']),immutable=True)
 require(result.get('state')=='complete_unscored' and result.get('attempted_requests')==2 and result.get('retries')==0,'MODEL_REQUEST_FAILED')
 require(result['records'][0].get('arithmetic_exact') is True,'ARITHMETIC_INCORRECT')
 return True

def retain_request_packet(raw,store):
 from guest_requests import validate_packet
 require(isinstance(raw,str) and len(raw.encode())<=8192,'CAPTURE_PACKET_SIZE')
 result=validate_packet(json.loads(raw))
 store.write('model-result.json',result,immutable=True)
 return result

def arm(b,scopes,state,store):
 remaining=int(state['restore_deadline']-time.time());require(remaining>900,'GUARDIAN_MARGIN')
 call(['systemd-run','--quiet','--unit='+scopes.guardian,'--property=Type=exec','--property=KillMode=control-group','--property=Restart=no','--property=TimeoutStopSec=30','--property=RuntimeMaxSec='+str(remaining+600),'/usr/bin/python3','-B',str(HERE/'model_trial.py'),'watch','--booking-id',b],15)
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
   row=bookings.get(b);now=int(time.time())
   require(row['state']=='reserved' and row['start_epoch']<=now<=row['start_epoch']+120,'LAUNCH_WINDOW')
   call(['systemd-run','--quiet','--unit='+scopes.owner,'--property=Type=exec','--property=KillMode=control-group','--property=Restart=no','--property=TimeoutStopSec=30','--property=RuntimeMaxSec='+str(row['end_epoch']-now+300),'/usr/bin/python3','-B',str(HERE/'model_trial.py'),'run','--booking-id',b],15)
   return {'state':'owner-launched','booking_id':b}
  if action=='watch':
   def alive(state):
    p=store.root/'model-intent.json'
    if p.exists() and state['phase'] not in {'restoring','restored','released','released-late'}:
     try:kernel_check(adapter,time.time()+4,store.read(p.name)['observed_epoch'])
     except Exception:
      store.write('model-guardian-stop.json',{'new_fault_or_monitor_failure':True,'observed_epoch':int(time.time())});return False
    return scopes.alive(state)
   return guard(store,adapter,owner=profile['owner'],owner_alive=alive,fence_owner=scopes.fence)
  require(action=='run' and scopes._show().get('MainPID')==str(os.getpid()) and scopes.alive({}),'OWNER_SCOPE')
  session=ExclusiveSession(store,adapter)
  try:
   session.begin(bookings.get(b),owner=profile['owner'],trial_seconds=profile['trial_seconds'])
   result=session.run_trial(owner=profile['owner'])
   store.write('model-terminal.json',{'schema':'b60-model-compatibility-terminal.v1','booking_id':b,'outcome':result['outcome'],'finished_epoch':int(time.time()),'restored':True,'model_result_present':(store.root/'model-result.json').exists(),'candidate_sha256':MODEL_SHA,'source_map_sha256':BASE_SHA,'capability_latency_milestone_accepted':False},immutable=True)
   return result
  except BaseException as error:
   # Do not auto-retry a model/device failure or repeat a failed restoration.
   # Independent guardian owns unfinished recovery under the once-only latch.
   store.write('model-owner-failure.json',{'failure_type':type(error).__name__,'failure_code':str(error) if type(error) is RuntimeError and str(error).replace('_','').isalnum() else 'UNCLASSIFIED','observed_epoch':int(time.time())})
   # No duplicate outer recovery/start. Independent guardian owns unfinished rescue.
   raise
 finally:adapter.boundary.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=('launch','run','watch'));p.add_argument('--booking-id',required=True);a=p.parse_args()
 try:initialize();print(json.dumps(operate(a.action,a.booking_id),sort_keys=True))
 except Exception as e:print(json.dumps({'state':'no_go','failure_type':type(e).__name__}));raise SystemExit(1)
