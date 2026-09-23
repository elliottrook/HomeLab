#!/usr/bin/env python3
"""Refresh only this integration, preserve other gateway work, protect custody.

Optional root reconciliation of one proven failed guest job issues a short-lived
one-use retry; it does not erase the failure or grant Aster a retry override.
"""
import argparse
import ast
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from deploy import CUSTODY, ROOT, SOURCE, ssh, write
from worker import snapshot_custody, write_json


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--retry-failed')
    parser.add_argument('--broker-only',action='store_true')
    args=parser.parse_args()
    os.umask(0o077)
    live=ssh('pct exec 104 -- cat /opt/aster-agent/aster_agent.py').decode()
    assert 'from lab_operations import' in live
    candidate=live
    if 'Current lab execution capability:' not in candidate:
        template=(ROOT/'services/aster-agent/aster_agent.py').read_text()
        start=template.index('    if request.persona == "sysadmin" and lab_operations.enabled:')
        end=template.index('    read_only_context = await',start)
        anchor='    read_only_context = await preload_read_only_context(request.messages, selected_tools)'
        assert candidate.count(anchor)==1
        candidate=candidate.replace(anchor,template[start:end]+anchor,1)
    ast.parse(candidate)
    module=(ROOT/'services/aster-agent/lab_operations.py').read_text()
    payload={'source':candidate,'module':module,'expected':hashlib.sha256(live.encode()).hexdigest()}
    code='''import ast,hashlib,json,pathlib,shutil,sqlite3,subprocess,time
p=PAYLOAD
c=sqlite3.connect('/var/lib/aster/lab-operations/jobs.sqlite3')
assert not c.execute("SELECT 1 FROM jobs WHERE state IN ('queued','running','unknown')").fetchone()
source=pathlib.Path('/opt/aster-agent/aster_agent.py')
assert hashlib.sha256(source.read_bytes()).hexdigest()==p['expected']
ast.parse(p['source']);ast.parse(p['module'])
backup=pathlib.Path('/opt/aster-agent/rollback-lab-refresh-'+str(int(time.time())));backup.mkdir(mode=0o700)
module=source.with_name('lab_operations.py')
shutil.copy2(source,backup/source.name);shutil.copy2(module,backup/module.name)
try:
 for path,data in ((source,p['source']),(module,p['module'])):
  temp=path.with_suffix('.candidate');temp.write_text(data);temp.chmod(0o644);temp.replace(path)
 subprocess.run(['systemctl','restart','aster-agent.service'],check=True)
 time.sleep(2)
 subprocess.run(['curl','-fsS','http://192.168.70.10:9120/health'],check=True,capture_output=True)
except Exception:
 shutil.copy2(backup/source.name,source);shutil.copy2(backup/module.name,module)
 subprocess.run(['systemctl','restart','aster-agent.service'])
 raise
print('gateway refreshed')
'''.replace('PAYLOAD',repr(payload),1)
    ssh('pct exec 104 -- python3 -',code.encode())
    if args.broker_only:
        print('Broker refreshed; gateway healthy',flush=True)
        return
    helper=(SOURCE/'guest_helper.py').read_text()
    code='import ast,pathlib\ns='+repr(helper)+"\nast.parse(s)\np=pathlib.Path('/usr/local/sbin/aster-lab-guest');p.write_text(s);p.chmod(0o755)\n"
    ssh('python3 -',code.encode())
    if args.retry_failed:
        import re
        assert re.fullmatch('[a-f0-9]{32}',args.retry_failed)
        code='''import json,pathlib,subprocess,time
jid=JOB
root=pathlib.Path('/var/lib/aster-lab-guest')
previous=json.loads((root/(jid+'.json')).read_text())
assert previous['result']['state']=='failed'
vmid=previous['target'].removeprefix('guest-')
active=json.loads(subprocess.check_output(['pvesh','get','/nodes/proxmox/tasks','--source','active','--output-format','json']))
assert not any(t.get('type')=='vzdump' for t in active)
assert not any(p.stat().st_mtime>=previous['started'] for p in pathlib.Path('/mnt/backups/dump').glob('vzdump-lxc-'+vmid+'-*.tar.zst'))
ticket=root/('.retry-'+previous['target'])
ticket.write_text(json.dumps({'job':jid,'expires':time.time()+600}));ticket.chmod(0o600)
print('failed guest job reconciled; one-use retry issued')
'''.replace('JOB',repr(args.retry_failed),1)
        ssh('python3 -',code.encode())
        code='''import sqlite3,time
jid=JOB
c=sqlite3.connect('/var/lib/aster/lab-operations/jobs.sqlite3')
assert c.execute('SELECT state FROM jobs WHERE id=?',(jid,)).fetchone()==('failed',)
c.execute('INSERT OR REPLACE INTO metadata VALUES (?,?)',('retry:'+jid,time.time()+600));c.commit()
'''.replace('JOB',repr(args.retry_failed),1)
        ssh('pct exec 104 -- python3 -',code.encode())
        ledger_path=CUSTODY/'state/capacity-reservations.json'
        ledger=json.loads(ledger_path.read_text())
        ledger.pop(args.retry_failed,None)
        write_json(ledger_path,ledger)
    write(CUSTODY/'worker.py',(SOURCE/'worker.py').read_text(),0o700)
    for relative in ('scripts/doctor.sh','scripts/check-aster-lab-operations.py', *('scripts/backup/'+name+'.sh' for name in ('opnsense','arista','proxmox','nut','observability','video-archiver'))):
        write(CUSTODY/'toolkit'/relative,(ROOT/relative).read_text(),0o700)
    count=snapshot_custody(CUSTODY,Path.home())
    subprocess.run(['launchctl','kickstart','-k',f'gui/{os.getuid()}/com.jason.aster-lab-worker'],check=True)
    print('Runtime refreshed; protected custody recovery bundle verified ('+str(count)+' bytes)',flush=True)


if __name__=='__main__': main()
