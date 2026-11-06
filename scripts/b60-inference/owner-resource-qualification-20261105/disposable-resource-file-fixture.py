"""Disposable actual systemd resource-file restore, never starts the fixture."""
import os,sys,subprocess,json
from pathlib import Path
sys.path.insert(0,'/usr/local/libexec/local-ai-lease/exclusive-session')
from host_exclusion import host_exclusion
from lab_hours_file_checkpoint import FileCheckpoint
R=Path('/var/lib/local-ai-lab');u='b60-resource-file-fixture-20261105.service';f=Path('/etc/systemd/system')/u;parent=Path('/run/systemd/system.control')/(u+'.d');paths=[parent/'50-CPUQuota.conf',parent/'50-MemoryMax.conf'];backup=R/'resource-file-fixture-20261105'
def call(a):
 p=subprocess.run(a,capture_output=True,text=True,timeout=20);assert p.returncode==0,'DISPOSABLE_RESOURCE_FILE_COMMAND';return p.stdout
with host_exclusion(R):
 assert json.loads(call(['/usr/local/sbin/local-ai-lease','status']))=={'state':'ready'} and not (R/'lease.lock').exists()
 assert not f.exists() and not parent.exists() and not backup.exists()
 f.write_text('[Unit]\nDescription=Disposable resource file recovery fixture\n[Service]\nType=oneshot\nExecStart=/usr/bin/true\n');f.chmod(0o644)
 try:
  call(['systemctl','daemon-reload']);call(['systemctl','set-property','--runtime',u,'CPUQuota=400%','MemoryMax=4G'])
  backup.mkdir(mode=0o700);cp=FileCheckpoint(backup/'files',allowed_roots=(),allowed_files=tuple(paths),expected_uid=0);receipt=cp.capture([str(p) for p in paths]);assert cp.verify(receipt)
  call(['systemctl','set-property','--runtime',u,'CPUQuota=10%','MemoryMax=256M'])
  assert 'CPUQuotaPerSecUSec=100ms' in call(['systemctl','show',u,'--property=CPUQuotaPerSecUSec'])
  cp.restore(receipt);assert cp.verify(receipt);call(['systemctl','daemon-reload'])
  raw=call(['systemctl','show',u,'--property=CPUQuotaPerSecUSec,MemoryMax,ActiveState,MainPID']);fields=dict(l.split('=',1) for l in raw.splitlines())
  assert fields=={'CPUQuotaPerSecUSec':'4s','MemoryMax':'4294967296','ActiveState':'inactive','MainPID':'0'}
  print(json.dumps({'state':'disposable-resource-file-restore-pass','effective_entry_limits_restored':True,'unit_never_started':True,'checkpoint_sha256':receipt,'properties':fields},sort_keys=True))
 finally:
  f.unlink(missing_ok=True)
  for p in paths:p.unlink(missing_ok=True)
  if parent.exists():assert not list(parent.iterdir());parent.rmdir()
  call(['systemctl','daemon-reload'])
