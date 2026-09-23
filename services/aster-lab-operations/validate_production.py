#!/usr/bin/env python3
"""Operator-seeded real-worker tests. Does not claim Companion JWT/UI validation."""
import argparse
import json
import subprocess
import time
import uuid

TARGETS=['doctor','opnsense','arista','proxmox','nut','observability','video-archiver',
         'guest-104','guest-109','guest-111','guest-113','guest-116']


def request(target=None, jid=None):
    if target:
        inner="import json; from lab_operations import LabOperations,Start; o=LabOperations(); print(json.dumps(o.ready().start(o.owner,Start(target="+repr(target)+",request_id="+repr('operator-validation-'+uuid.uuid4().hex)+"))))"
    else:
        inner="import json; from lab_operations import LabOperations; o=LabOperations(); print(json.dumps(o.ready().get(o.owner,"+repr(jid)+")))"
    code="import os,subprocess\nfrom pathlib import Path\nenv=dict(os.environ)\nfor line in Path('/etc/aster/lab-operations.env').read_text().splitlines():\n k,v=line.split('=',1);env[k]=v\nsubprocess.run(['runuser','-u','aster','--','/opt/aster-agent/venv/bin/python','-c',"+repr(inner)+"],cwd='/opt/aster-agent',env=env,check=True)\n"
    result=subprocess.run(['ssh','-o','BatchMode=yes','root@192.168.50.10','pct exec 104 -- python3 -'],
                          input=code.encode(),capture_output=True,timeout=30)
    if result.returncode:
        raise RuntimeError('Operator job request failed; inspect bounded queue status')
    return json.loads(result.stdout)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('targets',nargs='+',choices=TARGETS)
    args=parser.parse_args()
    for target in args.targets:
        started=time.time()
        job=request(target)
        if job['created']<started-5:
            raise SystemExit('Target returned an earlier job; wait for cooldown before counting another pass')
        print(json.dumps({'target':target,'id':job['id'],'state':job['state']}),flush=True)
        deadline=time.time()+7300
        while job['state'] in ('queued','running') and time.time()<deadline:
            time.sleep(15)
            job=request(jid=job['id'])
        result=job.get('result') or {}
        print(json.dumps({'target':target,'id':job['id'],'state':job['state'],
                          'code':result.get('code'),'bytes_verified':result.get('bytes_verified'),
                          'passed':result.get('passed'),'warnings':result.get('warnings'),'failures':result.get('failures')}),flush=True)
        if job['state']!='succeeded':
            raise SystemExit('Validation stopped: target did not produce a verified successful result')


if __name__=='__main__': main()
