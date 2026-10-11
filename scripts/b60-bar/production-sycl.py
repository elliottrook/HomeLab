#!/usr/bin/env python3
"""Proxmox: approved atomic SYCL activation or exact Vulkan recovery.

Independent host rollback timer must be armed before activation. Candidate
failure restores Vulkan; it never retries failed SYCL/GPU initialization.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0,'/run/b60-matched-sycl')
import guard
BASE='/opt/aster-sycl-b11429'
UNIT='/etc/systemd/system/aster-llama.service'
ROLLBACK=UNIT+'.pre-sycl-20261011'
OLD='6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e'
FAULT=r'GPU HANG|wedged|device lost|DMAR.*(fault|error)|IOMMU.*\sfault|Out of memory|oom-kill|BUG:|Oops:'

def run(*args,timeout=180,okay=(0,)):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if r.returncode not in okay: raise RuntimeError(f'command failed: {args[:5]} rc={r.returncode}')
    return r.stdout
def guest(*args,**kwargs):return run('pct','exec','110','--',*args,**kwargs)
def sha(path):return guest('sha256sum',path).split()[0]

def atomic_unit(source,expected_current,expected_source):
    code='''import hashlib,os,pathlib,sys
dst=pathlib.Path(sys.argv[1]);src=pathlib.Path(sys.argv[2])
assert hashlib.sha256(dst.read_bytes()).hexdigest()==sys.argv[3]
raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==sys.argv[4]
tmp=dst.with_name(dst.name+'.b60-atomic')
with os.fdopen(os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644),'wb') as f:
 f.write(raw);f.flush();os.fsync(f.fileno())
os.replace(tmp,dst)
'''
    guest('python3','-c',code,UNIT,source,expected_current,expected_source)
    guest('systemctl','daemon-reload')

def rollback():
    assert sha(ROLLBACK)==OLD and sha('/opt/llama.cpp-b11429/llama-server')==guard.ACCEPTED_BINARY_SHA256
    current=sha(UNIT)
    manifest=json.loads(guest('python3','-c',f'import json; print(json.dumps(json.load(open("{BASE}/manifest.json"))))'))
    assert current in [OLD,manifest['unit_sha256']], 'unknown unit; do not overwrite'
    if current!=OLD: atomic_unit(ROLLBACK,current,OLD)
    guard.execute_finalizer()
    print(run('pct','exec','114','--','python3','/run/b60-bar-validate-generation.py'),flush=True)
    print('EXACT VULKAN ROLLBACK VALIDATED',flush=True)

def activate(run_id):
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',run_id)
    assert run('systemctl','is-active','b60-sycl-promotion-restore.timer').strip()=='active'
    assert sha(UNIT)==OLD and sha(ROLLBACK)==OLD
    manifest=json.loads(guest('python3','-c',f'import json; print(json.dumps(json.load(open("{BASE}/manifest.json"))))'))
    assert manifest['rollback_unit_sha256']==OLD and manifest['volatile_dependencies'] is False
    assert sha(BASE+'/llama-sycl-fp16/llama-b11429/llama-server')==manifest['server_sha256']
    assert sha(BASE+'/llama-sycl-fp16/llama-b11429/libggml-sycl.so.0.26.0')==manifest['backend_sha256']
    assert sha('/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf')=='cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13'
    guest('python3','-c','import shutil; assert shutil.disk_usage("/").free>=20*1024**3')
    try:
        guest('systemctl','stop','aster-llama.service')
        time.sleep(30)
        atomic_unit(BASE+'/aster-llama.service',OLD,manifest['unit_sha256'])
        guest('systemctl','start','--no-block','aster-llama.service')
        deadline=time.monotonic()+330
        while time.monotonic()<deadline:
            state=guest('systemctl','is-active','aster-llama.service',okay=(0,3)).strip()
            if state in ['inactive','failed']:raise RuntimeError('SYCL failed; no retry')
            if state=='active':
                health=guest('curl','-fsS','--max-time','5','http://192.168.70.12:11435/health',okay=(0,7,22,28))
                if health and json.loads(health).get('status')=='ok':break
            time.sleep(3)
        else:raise RuntimeError('SYCL readiness timeout; no retry')
        assert sha(UNIT)==manifest['unit_sha256']
        assert guest('systemctl','show','aster-llama.service','-p','NRestarts','--value').strip()=='0'
        kernel=run('journalctl','-b','-k','--no-pager')
        assert kernel.strip() and not re.search(FAULT,kernel,re.I)
        assert run('readlink','/sys/bus/pci/devices/0000:04:00.0/driver').strip().endswith('/xe')
        assert 'BMG G21' in guest('vulkaninfo','--summary')
        print(run('python3','/run/b60-matched-sycl/record-backend-proof.py','--prefix',run_id,'--unit','aster-llama.service'),flush=True)
        print(run('pct','exec','114','--','python3','/run/b60-bar-validate-generation.py'),flush=True)
        proof={'completed_at':datetime.now(timezone.utc).isoformat(),'unit_sha256':manifest['unit_sha256'],
               'server_sha256':manifest['server_sha256'],'healthy':True,'restarts':0,'kernel_faults':False,
               'rollback_unit_sha256':OLD,'runtime_persistent':True}
        raw=(json.dumps(proof,sort_keys=True)+'\n').encode()
        path=Path('/var/lib/b60-inference/evidence')/(run_id+'-activation.json')
        with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
            f.write(raw);f.flush();os.fsync(f.fileno())
        print(json.dumps({'activation':proof,'sha256':hashlib.sha256(raw).hexdigest()}),flush=True)
    except BaseException:
        rollback()
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rollback',action='store_true')
    p.add_argument('--activate',action='store_true')
    p.add_argument('--run-id')
    a=p.parse_args();assert a.rollback!=a.activate
    if a.rollback:rollback()
    else:activate(a.run_id)
