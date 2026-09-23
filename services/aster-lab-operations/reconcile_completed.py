#!/usr/bin/env python3
"""Operator-only reconciliation of an uncertain job from verified native evidence."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from deploy import CUSTODY, ROOT, SOURCE, ssh, write
from worker import snapshot_custody, write_json, verify_config


def main():
    parser=argparse.ArgumentParser();parser.add_argument('job');args=parser.parse_args()
    assert re.fullmatch('[a-f0-9]{32}',args.job)
    os.umask(0o077)
    code='''import hashlib,json,pathlib,re
jid=JOB
record=json.loads((pathlib.Path('/var/lib/aster-lab-guest')/(jid+'.json')).read_text())
assert record['result']['state']=='succeeded'
name=record['archive']; assert re.fullmatch(r'vzdump-lxc-(104|109|111|113|116)-[0-9_\\-]+\\.tar\\.zst',name)
p=pathlib.Path('/mnt/backups/dump')/name
h=hashlib.sha256()
with p.open('rb') as f:
 while data:=f.read(1024*1024): h.update(data)
assert h.hexdigest()==record['sha256'] and p.stat().st_size==record['result']['bytes_verified']
print(json.dumps(record))
'''.replace('JOB',repr(args.job),1)
    record=json.loads(ssh('python3 -',code.encode(),timeout=300))
    result=record['result'];result.pop('artifact',None)
    # Unknown state prevents new claims while the parser is replaced.
    write(CUSTODY/'worker.py',(SOURCE/'worker.py').read_text(),0o700)
    write(CUSTODY/'toolkit/scripts/backup/proxmox.sh',(ROOT/'scripts/backup/proxmox.sh').read_text(),0o700)
    ledger_path=CUSTODY/'state/capacity-reservations.json'
    ledger=json.loads(ledger_path.read_text())
    ledger[args.job]={'artifact':record['archive'],'bytes_verified':result['bytes_verified'],'reserved':max(1024**3,int(result['bytes_verified']*1.2))}
    write_json(ledger_path,ledger)
    code='''import json,sqlite3,sys,time
sys.path.insert(0,'/opt/aster-agent')
from lab_operations import Result
jid=JOB
result=RESULT
target=TARGET
encoded=json.dumps(Result(**result).model_dump(),sort_keys=True)
c=sqlite3.connect('/var/lib/aster/lab-operations/jobs.sqlite3');c.execute('BEGIN IMMEDIATE')
row=c.execute('SELECT state,result,target FROM jobs WHERE id=?',(jid,)).fetchone()
assert row and row[0]=='unknown' and row[2]==target
c.execute('CREATE TABLE IF NOT EXISTS operator_reconciliations (job TEXT, prior_state TEXT, prior_result TEXT, at REAL, evidence TEXT)')
c.execute('INSERT INTO operator_reconciliations VALUES (?,?,?,?,?)',(jid,row[0],row[1],time.time(),'Native helper completion plus fresh archive SHA256 match'))
c.execute("UPDATE jobs SET state='succeeded',result=?,updated=? WHERE id=?",(encoded,time.time(),jid));c.commit()
print('Verified native completion reconciled; prior uncertainty retained in audit')
'''.replace('JOB',repr(args.job),1).replace('RESULT',repr(result),1).replace('TARGET',repr(record['target']),1)
    ssh('pct exec 104 -- /opt/aster-agent/venv/bin/python -',code.encode())
    # Protect the new helper policy/audit alongside the existing host config.
    started=time.time()
    with (CUSTODY/'host-recovery-backup.log').open('wb') as log:
        subprocess.run(['/bin/bash',str(ROOT/'scripts/backup/proxmox.sh')],stdout=log,stderr=log,check=True,timeout=300)
    verify_config('proxmox',Path.home()/'lab/private-backups/proxmox',started)
    count=snapshot_custody(CUSTODY,Path.home())
    subprocess.run(['launchctl','kickstart','-k',f'gui/{os.getuid()}/com.jason.aster-lab-worker'],check=True)
    print('Completion reconciled without another backup; parser fixed; host and worker recovery bundles verified ('+str(count)+' worker bytes)',flush=True)


if __name__=='__main__':main()
