"""Disposable low-resource kernel/cgroup fixture, no AI-stack effects."""
import os,sys,time,json,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,'/usr/local/libexec/local-ai-lease/exclusive-session')
from host_exclusion import host_exclusion
R=Path('/var/lib/local-ai-lab');probe=Path('/usr/local/libexec/local-ai-lease/recovery-qualification-20261105/b60_resource_probe.py')
B='b60-exclusive-20261105-day-r5';unit='b60-bounded-resource-fixture-20261105.service';state=Path('/var/lib/b60-resource-'+B);mount=Path('/run/b60-qualification')
def call(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=20);assert p.returncode==0,'DISPOSABLE_FIXED_COMMAND_FAILED';return p.stdout
with host_exclusion(R):
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'}
 assert not (R/'lease.lock').exists() and not Path('/run/local-ai-lab-operation.lock').exists()
 available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024;assert available>4*1024**3
 assert not state.exists() and not mount.exists()
 assert hashlib.sha256(probe.read_bytes()).hexdigest()=='4405832c82593e8beaaf941a4b6f6ca74f7fabb45acafa2bc934ec296087ba5d'
 try:
  call(['systemd-run','--quiet','--unit='+unit,'--property=Type=exec','--property=RuntimeMaxSec=45','--property=TimeoutStopSec=5','--property=KillMode=control-group','--property=Restart=no','--property=MemoryMax=384M','--property=MemorySwapMax=0','--property=CPUQuota=25%','--property=TasksMax=16','--property=NoNewPrivileges=yes','--property=PrivateNetwork=yes','--property=PrivateMounts=yes','--property=ProtectSystem=strict','--property=ProtectHome=yes','--property=PrivateTmp=yes','--property=TemporaryFileSystem=/run/b60-qualification:rw,size=16M,mode=0700','--property=StateDirectory=b60-resource-'+B,'--property=StateDirectoryMode=0700','/usr/bin/python3','-B',str(probe),'--booking-id',B])
  for _ in range(60):
   if (state/'probe.json').exists():break
   time.sleep(.2)
  result=json.loads((state/'probe.json').read_text());assert result['bytes_touched']==134217728 and result['tmpfs_bytes']==8388608 and result['tmpfs_verified'] is True
  fields=dict(l.split('=',1) for l in call(['systemctl','show',unit,'--property=ActiveState,MainPID,MemoryPeak,MemoryMax,CPUQuotaPerSecUSec,TasksMax']).splitlines())
  assert fields['ActiveState']=='active' and fields['MemoryMax']=='402653184' and fields['CPUQuotaPerSecUSec']=='250ms' and fields['TasksMax']=='16' and 134217728<=int(fields['MemoryPeak'])<=402653184
  pid=int(fields['MainPID']);assert os.readlink('/proc/'+str(pid)+'/ns/mnt')!=os.readlink('/proc/self/ns/mnt')
 finally:
  subprocess.run(['systemctl','stop',unit],capture_output=True,timeout=15)
 assert not Path('/proc/'+str(pid)).exists()
 after=dict(l.split('=',1) for l in call(['systemctl','show',unit,'--property=ActiveState,MainPID,TasksCurrent']).splitlines());assert after['ActiveState'] in {'inactive','failed'} and after['MainPID']=='0' and after['TasksCurrent'] in {'0','','[not set]'}
 assert not any(l.split()[4]==str(mount) for l in Path('/proc/self/mountinfo').read_text().splitlines())
 if mount.exists():assert mount.is_dir() and not mount.is_symlink() and not list(mount.iterdir());mount.rmdir()
 assert not mount.exists()
 print(json.dumps({'state':'disposable-bounded-resource-pass','host_memory_available_bytes':available,'observed_cgroup':fields,'scope_after_stop':after,'private_mount_namespace_verified':True,'global_mount_absent':True,'ai_stack_changed':False,'model_called':False},sort_keys=True))
