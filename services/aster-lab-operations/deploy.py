#!/usr/bin/env python3
"""Approved, resumable first installation; never prints credential material.

Installs doctor-only at the broker. Backup capabilities remain disabled until
production verification. Run with platform permission for the Mac custody path.
"""
import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path
from build_candidate import patch

HOST = 'root@192.168.50.10'
ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
CUSTODY = Path.home()/'Library/Application Support/AsterLab'


def ssh(command, data=None, timeout=120):
    proc = subprocess.run(['ssh','-o','BatchMode=yes',HOST,command], input=data,
                          capture_output=True, timeout=timeout)
    if proc.returncode:
        if CUSTODY.is_dir():
            write(CUSTODY/'deployment-error.log',proc.stderr.decode(errors='replace'))
        raise RuntimeError('Remote deployment step failed; inspect protected operator state')
    return proc.stdout


def write(path, text, mode=0o600):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    path.write_text(text)
    path.chmod(mode)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--owner',required=True)
    args=parser.parse_args()
    if not re.fullmatch('[a-f0-9]{64}',args.owner):
        raise SystemExit('Expected a verified owner hash')
    os.umask(0o077)
    CUSTODY.mkdir(parents=True,exist_ok=True,mode=0o700)
    CUSTODY.chmod(0o700)
    state_file=CUSTODY/'installation.json'
    state=json.loads(state_file.read_text()) if state_file.exists() else {}
    if not state.get('checkpoint'):
        print('Creating and verifying the LXC 104 recovery checkpoint',flush=True)
        checkpoint_code='''import subprocess, pathlib, time, json, hashlib
root=pathlib.Path('/mnt/backups/dump')
before=set(root.glob('vzdump-lxc-104-*.tar.zst'))
with open('/root/aster-lab-checkpoint.log','wb') as log:
 subprocess.run(['/usr/bin/vzdump','104','--storage','backups','--mode','snapshot','--compress','zstd','--remove','0','--prune-backups','keep-all=1','--lockwait','0','--bwlimit','51200','--zstd','1'],check=True,stdout=log,stderr=log)
 files=set(root.glob('vzdump-lxc-104-*.tar.zst'))-before
 assert len(files)==1
 archive=files.pop()
 subprocess.run(['/usr/bin/zstd','-t',str(archive)],check=True,stdout=log,stderr=log)
 digest=hashlib.sha256()
 with archive.open('rb') as f:
  while data:=f.read(1024*1024): digest.update(data)
 print(json.dumps({'archive':archive.name,'bytes':archive.stat().st_size,'sha256':digest.hexdigest()}))
'''
        state['checkpoint']=json.loads(ssh('python3 -',checkpoint_code.encode(),timeout=5400))
        write(state_file,json.dumps(state))
        print('Checkpoint archive integrity verified',flush=True)
    live=ssh('pct exec 104 -- cat /opt/aster-agent/aster_agent.py').decode()
    if not state.get('gateway'):
        candidate=patch(live,(ROOT/'services/aster-agent/aster_agent.py').read_text())
        worker_key=secrets.token_urlsafe(48)
        config={'url':'https://aster.elliottrook.com','worker_key':worker_key,
                'repository':str(CUSTODY/'toolkit'), 'state':str(CUSTODY/'state'),
                'home':str(Path.home()),'targets':['doctor'], 'guest_key':str(CUSTODY/'guest_ed25519')}
        write(CUSTODY/'worker.json',json.dumps(config))
        rollback='/opt/aster-agent/rollback-lab-operations-'+time.strftime('%Y%m%d-%H%M%S')
        payload={
            'expected':hashlib.sha256(live.encode()).hexdigest(), 'candidate':candidate,
            'module':(ROOT/'services/aster-agent/lab_operations.py').read_text(),
            'dropin':(SOURCE/'systemd/aster-lab-operations.conf').read_text(),
            'environment':f'ASTER_LAB_OWNER={args.owner}\nASTER_LAB_WORKER_KEY={worker_key}\nASTER_LAB_TARGETS=doctor\n',
            'rollback':rollback,
        }
        # File values travel over encrypted stdin, never shell arguments/logs.
        code='''import ast, hashlib, json, pathlib, shutil, subprocess, time
p=PAYLOAD
source=pathlib.Path('/opt/aster-agent/aster_agent.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()==p['expected'], 'Live source changed'
ast.parse(p['candidate']); ast.parse(p['module'])
rollback=pathlib.Path(p['rollback']); rollback.mkdir(mode=0o700)
shutil.copy2(source,rollback/'aster_agent.py')
env=pathlib.Path('/etc/aster/lab-operations.env')
drop=pathlib.Path('/etc/systemd/system/aster-agent.service.d/lab-operations.conf')
assert not env.exists() and not drop.exists(), 'Integration already configured'
try:
 module=source.with_name('lab_operations.py'); module.write_text(p['module']); module.chmod(0o644)
 temp=source.with_suffix('.lab-candidate'); temp.write_text(p['candidate']); temp.chmod(0o644); temp.replace(source)
 env.write_text(p['environment']); env.chmod(0o600)
 drop.parent.mkdir(exist_ok=True); drop.write_text(p['dropin']); drop.chmod(0o644)
 subprocess.run(['systemctl','daemon-reload'],check=True)
 subprocess.run(['systemctl','restart','aster-agent.service'],check=True)
 for i in range(30):
  result=subprocess.run(['curl','-fsS','http://192.168.70.10:9120/health'],capture_output=True)
  if result.returncode==0: break
  time.sleep(1)
 else: raise RuntimeError('Gateway health failed')
 print('gateway healthy')
except Exception:
 shutil.copy2(rollback/'aster_agent.py',source)
 env.unlink(missing_ok=True); drop.unlink(missing_ok=True)
 subprocess.run(['systemctl','daemon-reload']); subprocess.run(['systemctl','restart','aster-agent.service'])
 raise
'''.replace('PAYLOAD',repr(payload),1)
        ssh('pct exec 104 -- python3 -',code.encode())
        state['gateway']={'rollback':rollback,'sha256':hashlib.sha256(candidate.encode()).hexdigest()}
        write(state_file,json.dumps(state))
        print('Doctor-only gateway installed; prior source retained',flush=True)
    # Install pinned executable files without overwriting operator SSH custody.
    for relative in ['scripts/doctor.sh','scripts/check-aster-lab-operations.py','scripts/lib/output.sh','configs/services.conf',
                     *['scripts/backup/'+name+'.sh' for name in ('opnsense','arista','proxmox','nut','observability','video-archiver')]]:
        write(CUSTODY/'toolkit'/relative,(ROOT/relative).read_text(),0o700 if relative.endswith('.sh') else 0o600)
    write(CUSTODY/'worker.py',(SOURCE/'worker.py').read_text(),0o700)
    label=Path.home()/'Library/LaunchAgents/com.jason.aster-lab-worker.plist'
    write(label,(SOURCE/'launchd/com.jason.aster-lab-worker.plist').read_text(),0o644)
    if not state.get('worker'):
        subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(label)],check=True)
        state['worker']=True
        write(state_file,json.dumps(state))
    print('Mac worker installed; doctor-only mode active',flush=True)


if __name__=='__main__': main()
