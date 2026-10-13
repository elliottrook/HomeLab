#!/usr/bin/env python3
"""Read-only persistent SYCL regression/soak checks with sanitized evidence."""
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

BASE='/opt/aster-sycl-b11429'
FAULT=r'GPU HANG|wedged|device lost|DMAR.*(fault|error)|IOMMU.*\sfault|Out of memory|oom-kill|BUG:|Oops:'
def run(*args,timeout=180,okay=(0,)):
 r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
 assert r.returncode in okay,f'validation command failed {args[:5]} rc={r.returncode}'
 return r.stdout
def guest(n,*args,**kw):return run('pct','exec',str(n),'--',*args,**kw)
def gates():
 m=json.loads(guest(110,'python3','-c',f'import json; print(json.dumps(json.load(open("{BASE}/manifest.json"))))'))
 assert guest(110,'sha256sum','/etc/systemd/system/aster-llama.service').split()[0]==m['unit_sha256']
 assert guest(110,'sha256sum',BASE+'/llama-sycl-fp16/llama-b11429/llama-server').split()[0]==m['server_sha256']
 assert guest(110,'systemctl','is-active','aster-llama.service').strip()=='active'
 assert guest(110,'systemctl','show','aster-llama.service','-p','NRestarts','--value').strip()=='0'
 assert json.loads(guest(110,'curl','-fsS','--max-time','10','http://192.168.70.12:11435/health'))['status']=='ok'
 assert json.loads(guest(114,'curl','-fsS','--max-time','10','http://192.168.70.10:9120/health'))['status']=='ok'
 kernel=run('journalctl','-b','-k','--no-pager');assert kernel.strip() and not re.search(FAULT,kernel,re.I)
 assert run('readlink','/sys/bus/pci/devices/0000:04:00.0/driver').strip().endswith('/xe')
 assert 'BMG G21' in guest(110,'vulkaninfo','--summary')
 telemetry=dict(l.split('=',1) for l in guest(110,'sh','/run/b60-bar-telemetry.sh').splitlines())
 assert int(telemetry['ram_available_kib'])*1024>=4*1024**3
 assert 25669140480-int(telemetry['vram_resident_kib'])*1024>=2*1024**3
 assert int(telemetry['gpu_temp_pkg_millic'])<80000 and int(telemetry['gpu_temp_vram_millic'])<80000
 guest(110,'python3','-c','import shutil; assert shutil.disk_usage("/").free>=20*1024**3')
 for unit in ['news-aggregator-ingest','news-aggregator-digest']:
  assert guest(114,'systemctl','is-enabled',unit+'.timer',okay=(1,)).strip()=='disabled'
  assert guest(114,'systemctl','is-active',unit+'.service',okay=(3,)).strip()=='inactive'
 return {'at':datetime.now(timezone.utc).isoformat(),'unit_sha256':m['unit_sha256'],'telemetry':telemetry,'healthy':True,'kernel_faults':False,'restarts':0}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--soak-seconds',type=int,default=0);p.add_argument('--regression',action='store_true');a=p.parse_args()
 assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',a.run_id) and 0<=a.soak_seconds<=600
 out=Path('/var/lib/b60-inference/evidence')/(a.run_id+'-production-validation.json');assert not out.exists()
 checks=[gates()]
 print(guest(114,'python3','/run/b60-bar-validate-generation.py'),flush=True)
 if a.regression:
  target='/var/lib/b60-inference/evidence/'+a.run_id+'-regression.json'
  print(guest(114,'timeout','180','python3','/run/b60-matched-sycl/runner.py','--endpoint','http://192.168.70.12:11435','--api-key-file','/root/.news-aggregator-llama-key','--cases','/run/b60-matched-sycl/cases.json','--label',a.run_id,'--output',target,'--max-tokens','256','--timeout','60','--fail-fast-runtime',timeout=190,okay=(0,1)),flush=True)
  print(guest(114,'python3','-c','import json,sys; d=json.load(open(sys.argv[1])); assert len(d["results"])==16 and d["pass_count"]>=12; assert all(r["elapsed_seconds"] is not None for r in d["results"]); assert {r["id"] for r in d["results"] if not r["passed"]}<={"stale-news","contradictory-sources","missing-evidence","private-public-join"}; print(json.dumps({"pass_count":d["pass_count"],"total":16,"new_failures":False}))',target),flush=True)
  checks.append(gates())
 deadline=time.monotonic()+a.soak_seconds
 while time.monotonic()<deadline:
  time.sleep(min(30,max(0,deadline-time.monotonic())))
  checks.append(gates())
  print(json.dumps(checks[-1]),flush=True)
 raw=(json.dumps({'checks':checks,'bounded_soak_seconds':a.soak_seconds,'regression':a.regression},sort_keys=True)+'\n').encode()
 with os.fdopen(os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 print(json.dumps({'evidence':str(out),'sha256':hashlib.sha256(raw).hexdigest(),'passed':True}),flush=True)
if __name__=='__main__':main()
