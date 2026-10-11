#!/usr/bin/env python3
"""Capture selected non-secret process mappings and exact-invocation GPU proof."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def run(*args):
    return subprocess.check_output(args,text=True,timeout=120)
def guest(*args):
    return run('pct','exec','110','--',*args)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prefix',required=True)
args=parser.parse_args()
assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,95}',args.prefix)
assert guest('systemctl','is-active','aster-b60-candidate.service').strip()=='active'
inv=guest('systemctl','show','aster-b60-candidate.service','-p','InvocationID','--value').strip()
assert re.fullmatch(r'[0-9a-f]{32}',inv)
pid=int(guest('systemctl','show','aster-b60-candidate.service','-p','MainPID','--value'))
assert pid>1
maps=guest('python3','-c','import pathlib,sys,json; p=pathlib.Path("/proc")/sys.argv[1]/"maps"; print(json.dumps(sorted({s.split()[-1] for s in p.read_text().splitlines() if any(k in s for k in ["libze_loader", "libze_intel_gpu", "libggml-sycl", "libsycl.so"])})))',str(pid))
mapped=json.loads(maps)
assert any(p.endswith('/libze_loader.so.1.33.1') for p in mapped)
assert any('libggml-sycl' in p for p in mapped)
backend=next(p for p in mapped if p.endswith('/libggml-sycl.so.0.26.0'))
precision='fp16' if '/llama-sycl-fp16/' in backend else 'fp32'
backend_sha=guest('sha256sum',backend).split()[0]
assert backend_sha=={'fp16':'58757946256db139bab7ddab56dbe6e8d5503bb41518eb25bfc734c175c68591',
                    'fp32':'d267ea962c1166e964cc7bb771a9b7dd7c9b1405d5c5156463995a9f4e1da2d7'}[precision]
selected_env=json.loads(guest('python3','-c','import json,pathlib,sys; raw=(pathlib.Path("/proc")/sys.argv[1]/"environ").read_bytes(); allowed={"GGML_SYCL_ENABLE_FUSION","ONEAPI_DEVICE_SELECTOR"}; print(json.dumps({p.split("=",1)[0]:p.split("=",1)[1] for b in raw.split(bytes([0])) if b and "=" in (p:=b.decode()) and p.split("=",1)[0] in allowed}))',str(pid)))
assert selected_env.get('ONEAPI_DEVICE_SELECTOR')=='level_zero:gpu'
log=guest('journalctl','_SYSTEMD_INVOCATION_ID='+inv,'--no-pager')
offload=re.search(r'offloaded (\d+)/(\d+) layers',log)
assert offload and offload.group(1)==offload.group(2)
assert 'SYCL0 (Intel(R) Arc(TM) Pro B60 Graphics)' in log
safe=[s for s in log.splitlines() if any(k in s for k in ['using device SYCL0','offloaded','model buffer size','output buffer size','KV buffer size','RS buffer size','compute buffer size'])]
data=dict(collected_at=datetime.now(timezone.utc).isoformat(),invocation_id=inv,pid=pid,
          candidate_precision=precision,backend_sha256=backend_sha,selected_backend_environment=selected_env,
          mapped_backend_libraries=mapped,offloaded_layers=int(offload.group(1)),
          total_layers=int(offload.group(2)),startup_facts=safe,
          limitations=['All transformer layers offloaded; CPU-mapped and host buffers still exist.'])
raw=(json.dumps(data,sort_keys=True)+'\n').encode()
path=Path('/var/lib/b60-inference/evidence')/(args.prefix+'-backend-proof.json')
with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
    f.write(raw); f.flush(); os.fsync(f.fileno())
print(json.dumps(dict(proof=data,sha256=hashlib.sha256(raw).hexdigest()),sort_keys=True))
