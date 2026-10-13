#!/usr/bin/env python3
"""Archive the exact loader-only attempt's sanitized startup and guarded abort."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

def run(*args):
    return subprocess.check_output(args,text=True,timeout=120)
def guest(n,*args):
    return run('pct','exec',str(n),'--',*args)
def immutable(path,text):
    raw=text.encode()
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return hashlib.sha256(raw).hexdigest()
invocation='1cfae5fc97f045fba5f67f6059481671'
log=guest(110,'journalctl','_SYSTEMD_INVOCATION_ID='+invocation,'--no-pager')
assert 'model loaded' in log and 'listening on' in log
assert 'UR_RESULT_ERROR_UNSUPPORTED_FEATURE' not in log
assert 'offloaded' not in log
safe='\n'.join(s for s in log.splitlines() if any(k in s for k in ['model loaded','listening on','initializing','verbosity =','threadpool init']))+'\n'
root=Path('/var/lib/b60-inference/evidence')
trace_hash=immutable(root/'loader-1331-startup-20261010.log',safe)
preflight=json.loads(Path('/run/b60-matched-sycl/preflight-loader-retry.json').read_text())
assert guest(110,'systemctl','is-active','aster-llama.service').strip()=='active'
assert json.loads(guest(110,'curl','-fsS','--max-time','10','http://192.168.70.12:11435/health'))['status']=='ok'
state=guest(110,'systemctl','show','aster-b60-candidate.service','-p','ActiveState','--value').strip()
assert state=='inactive'
kernel=run('journalctl','-b','-k','--no-pager')
import re
assert kernel.strip() and not re.search(r'GPU HANG|wedged|device lost|DMAR.*(fault|error)|IOMMU.*\sfault|Out of memory|oom-kill|BUG:|Oops:',kernel,re.I)
record=dict(invocation_id=invocation,preflight=preflight,private_loader_version='1.33.1',
    package_sha256='298d6d3656a13f112497f557be2cb557efb67374bc7d069aa77a9115db909e1d',
    loader_sha256='a4859c17183add6412c48d44d0f356f8ef5d7b43ae35ed253074f670a6879d23',
    actual_loader_mapping_verified=True, fusion_enabled=False, model_loaded=True,
    listening=True,full_gpu_offload_proven=False,abort_reason='required offload information absent at default verbosity 3',
    candidate_requests=0,sycl_measured_repetitions=0,speed_improvement=None,
    automatic_retry=False,production_restored_and_generation_validated_at='2026-10-10T22:50:30-07:00',
    news_schedules='stopped and disabled until owner resumes',kernel_faults=False,
    sanitized_trace_sha256=trace_hash,
    fresh_vulkan_confirmation=dict(pass_count=12,case_count=16,median_seconds=2.4922815,
      sha256='e2086fd83e9c76b7efaf83876265935d9787763ca48a54f1ff9672fc0daf97fa'))
digest=immutable(root/'loader-1331-outcome-20261010.json',json.dumps(record,sort_keys=True)+'\n')
print(json.dumps(dict(outcome=record,record_sha256=digest),sort_keys=True))
