#!/usr/bin/env python3
"""Provision restricted guest identity and activate approved backup adapters.

Requires platform permission for protected Mac custody and the Stream A scope.
Refuses to interrupt an active or uncertain job. Never prints credentials.
"""
import json
import os
import subprocess
from pathlib import Path
from deploy import CUSTODY, ROOT, SOURCE, ssh, write

TARGETS=['doctor','opnsense','arista','proxmox','nut','observability','video-archiver',
         'guest-104','guest-109','guest-111','guest-113','guest-116']


def main():
    os.umask(0o077)
    # Inspection is schema restricted: no owner, lease or credential output.
    status=ssh("pct exec 104 -- python3 -",b"import sqlite3,json\nc=sqlite3.connect('/var/lib/aster/lab-operations/jobs.sqlite3'); print(json.dumps(c.execute(\"SELECT state,COUNT(*) FROM jobs WHERE state IN ('queued','running','unknown') GROUP BY state\").fetchall()))\n")
    if json.loads(status):
        raise SystemExit('Active or uncertain lab job: finish/reconcile before activation')
    key=CUSTODY/'guest_ed25519'
    if not key.exists():
        subprocess.run(['ssh-keygen','-q','-t','ed25519','-N','','-C','ai-lab-backup','-f',str(key)],check=True)
    public=key.with_suffix('.pub').read_text().strip()
    payload={'public':public,'helper':(SOURCE/'guest_helper.py').read_text(),
             'sudoers':(SOURCE/'proxmox-sudoers').read_text()}
    code='''import ast,json,os,pathlib,pwd,subprocess
p=PAYLOAD
ast.parse(p['helper'])
marker=pathlib.Path('/var/lib/aster-lab-guest/.managed')
try:
 pwd.getpwnam('ai-lab-backup')
 assert marker.exists(), 'Existing identity is not owned by this integration'
except KeyError: subprocess.run(['useradd','--system','--create-home','--home-dir','/var/lib/ai-lab-backup','--shell','/bin/sh','ai-lab-backup'],check=True)
marker.parent.mkdir(exist_ok=True,mode=0o700); marker.write_text('aster-lab-operations\\n'); marker.chmod(0o600)
home=pathlib.Path('/var/lib/ai-lab-backup'); home.chmod(0o755); os.chown(home,0,0)
keys=home/'.ssh'; keys.mkdir(exist_ok=True); keys.chmod(0o755); os.chown(keys,0,0)
wrapper=pathlib.Path('/usr/local/sbin/aster-lab-guest-ssh')
wrapper.write_text('#!/bin/sh\\n[ -z "$SSH_ORIGINAL_COMMAND" ] || exit 126\\nexec sudo -n /usr/local/sbin/aster-lab-guest\\n'); wrapper.chmod(0o755)
helper=pathlib.Path('/usr/local/sbin/aster-lab-guest'); helper.write_text(p['helper']); helper.chmod(0o755)
sudo=pathlib.Path('/etc/sudoers.d/aster-lab-backup'); sudo.write_text(p['sudoers']); sudo.chmod(0o440)
subprocess.run(['/usr/sbin/visudo','-cf',str(sudo)],check=True,capture_output=True)
address=os.environ['SSH_CONNECTION'].split()[0]
assert all(c in '0123456789.' for c in address)
authorized=keys/'authorized_keys'
authorized.write_text('from="'+address+'",restrict,command="/usr/local/sbin/aster-lab-guest-ssh" '+p['public']+'\\n'); authorized.chmod(0o644); os.chown(authorized,0,0)
print('restricted guest identity installed')
'''.replace('PAYLOAD',repr(payload),1)
    ssh('python3 -',code.encode())
    print('Restricted guest identity installed; no shell or forwarding',flush=True)
    # Deny proof: an explicit remote command must not execute.
    command=['ssh','-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','ConnectTimeout=8','-T','-i',str(key),'ai-lab-backup@192.168.50.10']
    denied=subprocess.run(command+['id'],capture_output=True,timeout=20)
    if denied.returncode != 126 or denied.stdout:
        raise RuntimeError('Forced-command denial proof failed')
    denied=subprocess.run(command,input=b'{"target":"guest-110","id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',capture_output=True,timeout=20)
    if json.loads(denied.stdout).get('code')!='disabled':
        raise RuntimeError('Unknown target denial proof failed')
    config=json.loads((CUSTODY/'worker.json').read_text())
    config['targets']=TARGETS
    write(CUSTODY/'worker.json',json.dumps(config))
    write(CUSTODY/'worker.py',(SOURCE/'worker.py').read_text(),0o700)
    for relative in ('scripts/doctor.sh','scripts/check-aster-lab-operations.py'):
        write(CUSTODY/'toolkit'/relative,(ROOT/relative).read_text(),0o700)
    # Replace only the target line; preserve identity and credential values.
    code='''from pathlib import Path
import subprocess
targets=TARGET_LIST
p=Path('/etc/aster/lab-operations.env')
s=p.read_text()
s='\\n'.join('ASTER_LAB_TARGETS='+','.join(targets) if line.startswith('ASTER_LAB_TARGETS=') else line for line in s.splitlines())+'\\n'
p.write_text(s);p.chmod(0o600)
subprocess.run(['systemctl','restart','aster-agent.service'],check=True)
'''.replace('TARGET_LIST',repr(TARGETS),1)
    ssh('pct exec 104 -- python3 -',code.encode())
    subprocess.run(['launchctl','kickstart','-k',f'gui/{os.getuid()}/com.jason.aster-lab-worker'],check=True)
    print('Backup adapters enabled for production validation',flush=True)


if __name__=='__main__': main()
