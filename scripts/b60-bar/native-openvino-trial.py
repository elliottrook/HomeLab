#!/usr/bin/env python3
"""One guarded native deployment comparison, exact accepted SYCL recovery."""
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo
import re
import signal
import sys
import time

sys.path.insert(0,'/run/b60-matched-sycl')
import importlib.util
CODE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('prod',CODE/'production-sycl.py')
prod=importlib.util.module_from_spec(spec);spec.loader.exec_module(prod)
spec=importlib.util.spec_from_file_location('verify',CODE/'verify-production-sycl.py')
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
ROOT='/run/b60-matched-sycl'
RAM='/dev/shm/b60-openvino-runtime-20261011'
CURRENT_UNIT='aster-llama.service'
def restore_after_trial():
 prod.restore_sycl()
 run('systemctl','stop','b60-openvino-restore.timer')
def run(*args,**kw):return prod.run(*args,**kw)
def guest(n,*args,**kw):return run('pct','exec',str(n),'--',*args,**kw)
def kernel_gate():
 assert not json.loads(run('pvesh','get','/nodes/proxmox/tasks','--source','active','--typefilter','vzdump','--output-format','json')),'active backup I/O; no benchmark'
 k=run('journalctl','-b','-k','--no-pager');assert k.strip() and not re.search(prod.FAULT,k,re.I)
 guest(110,'python3','-c','import shutil; assert shutil.disk_usage("/").free>=20*1024**3; m=dict(l.split(":",1) for l in open("/proc/meminfo")); assert int(m["MemAvailable"].split()[0])*1024>=4*1024**3')
 t=dict(l.split('=',1) for l in guest(110,'sh','/run/b60-bar-telemetry.sh',CURRENT_UNIT).splitlines())
 assert 25669140480-int(t['vram_resident_kib'])*1024>=2*1024**3
 assert 0<int(t['gpu_temp_pkg_millic'])<80000 and 0<int(t['gpu_temp_vram_millic'])<80000
 return t
def workflow(run_id,label,fixture):
 kernel_gate();target=f'/var/lib/b60-inference/evidence/{run_id}-{label}-{fixture}.json'
 fixed=['--fixed-length-decode'] if fixture=='b60-tg128-cold' else []
 print(guest(114,'timeout','420','python3','/run/b60-workflow/runner.py','--fixtures','/run/b60-workflow/synthetic-fixtures.json','--fixture',fixture,'--endpoint','http://192.168.70.12:11435','--api-key-file','/root/.news-aggregator-llama-key','--output',target,'--execute','--allow-production-endpoint','--stop-on-incorrect',*fixed,timeout=430,okay=(0,1)),flush=True)
 print(guest(114,'python3','-c','import json,sys,statistics; d=json.load(open(sys.argv[1])); assert d["health_passed"] and len(d["samples"])==12 and all(s["correct"] for s in d["samples"]); s=[s for s in d["samples"] if s["phase"]=="decode" and s["control_role"]=="measured"]; assert len(s)==5 and all(r["tokens"]>0 and r["tokens_per_second"]>0 for r in s); print(json.dumps({"fixture":d["fixture"],"tokens":[r["tokens"] for r in s],"median_latency_seconds":statistics.median(r["seconds"] for r in s),"median_decode_tps":statistics.median(r["tokens_per_second"] for r in s),"passed":True}))',target),flush=True)
 kernel_gate()
def main():
 global CURRENT_UNIT
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--accepted-unit-sha256',required=True);a=p.parse_args()
 assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,50}',a.run_id) and re.fullmatch(r'[0-9a-f]{64}',a.accepted_unit_sha256)
 acceptance=json.loads(Path('/var/lib/b60-inference/evidence/20261011-sycl-production-accepted.json').read_text())
 assert acceptance['accepted'] and acceptance['unit_sha256']==a.accepted_unit_sha256 and acceptance['runtime_persistent']
 local=datetime.now(ZoneInfo('America/Vancouver'))
 boundary=local.replace(hour=2,minute=30,second=0,microsecond=0)
 if local<boundary:assert (boundary-local).total_seconds()>35*60,'cannot benchmark across scheduled 02:30 backup boundary'
 assert run('systemctl','is-active','b60-openvino-restore.timer').strip()=='active'
 pre=json.loads(Path(ROOT+'/preflight-exclusive-'+a.run_id+'.json').read_text())
 assert pre['unit_sha256']==a.accepted_unit_sha256 and pre['binary_sha256']=='0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
 age=(datetime.now(timezone.utc)-datetime.fromisoformat(pre['collected_at'])).total_seconds();assert 0<=age<=300
 verify.gates();deadline=time.monotonic()+1800
 touched=False;recovered=False
 def interrupted(signum,frame):raise RuntimeError('bounded controller interrupted')
 signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
 fixtures=['b60-tg128-cold','aster-grounded-retrieval','aster-context-8k']
 try:
  for fixture in fixtures:workflow(a.run_id,'sycl-pre',fixture)
  assert time.monotonic()+1200<deadline,'insufficient candidate/recovery time'
  touched=True;guest(110,'systemctl','stop','aster-llama.service');time.sleep(30)
  libs=RAM+'/opencl/usr/lib/x86_64-linux-gnu:/opt/aster-sycl-b11429/driver/usr/local/lib:/opt/aster-sycl-b11429/driver/usr/lib/x86_64-linux-gnu:'+RAM+'/site/openvino/libs:/opt/aster-sycl-b11429/oneapi/usr/lib/x86_64-linux-gnu'
  guest(110,'systemd-run','--unit=aster-b60-candidate','--property=User=ollama','--property=Group=ollama','--property=SupplementaryGroups=video render','--property=Restart=no','--property=RuntimeMaxSec=900','--property=TimeoutStopSec=30','--property=LimitCORE=0','--setenv=LD_LIBRARY_PATH='+libs,'--setenv=OCL_ICD_VENDORS='+RAM+'/vendors','--setenv=OMP_NUM_THREADS=4','/usr/bin/python3','/run/b60-openvino-trial-server.py','--execute')
  CURRENT_UNIT='aster-b60-candidate.service'
  ready=time.monotonic()+480
  while time.monotonic()<ready:
   state=guest(110,'systemctl','is-active','aster-b60-candidate.service',okay=(0,3)).strip()
   if state in ['failed','inactive']:raise RuntimeError('native startup failed; no automatic retry')
   health=guest(110,'curl','-fsS','--max-time','3','http://192.168.70.12:11435/health',okay=(0,7,22,28))
   kernel_gate()
   if health and json.loads(health).get('status')=='ok':break
   time.sleep(5)
  else:raise RuntimeError('native startup deadline; no retry')
  assert int(kernel_gate()['vram_resident_kib'])>0,'native GPU telemetry unavailable'
  inv=guest(110,'systemctl','show','aster-b60-candidate.service','-p','InvocationID','--value').strip()
  log=guest(110,'journalctl','_SYSTEMD_INVOCATION_ID='+inv,'--no-pager')
  safe=[l for l in log.splitlines() if '"native_runtime"' in l or '"native_ready"' in l];assert len(safe)==2
  print('\n'.join(safe),flush=True)
  pid=guest(110,'systemctl','show','aster-b60-candidate.service','-p','MainPID','--value').strip()
  mapped=json.loads(guest(110,'python3','-c','import pathlib,json,sys; print(json.dumps(sorted({s.split()[-1] for s in (pathlib.Path("/proc")/sys.argv[1]/"maps").read_text().splitlines() if any(k in s for k in ["libigdrcl","libOpenCL","libopenvino_intel_gpu_plugin"])})))',pid))
  assert any('libigdrcl' in v and v.startswith(RAM) for v in mapped) and any('libopenvino_intel_gpu_plugin' in v and v.startswith(RAM) for v in mapped)
  mapped_hashes={v:guest(110,'sha256sum',v).split()[0] for v in mapped}
  proof={'invocation':inv,'pid':pid,'mapped_native_libraries':mapped_hashes,'startup':safe,'model_revision':'ee5a3761d4524966dd6c1f1037694ebc581cb196','quantization_change':True,'cpu_model_fallback':False,'prefix_cache':False,'mtp':False,'accepted_sycl_unit_sha256':a.accepted_unit_sha256}
  raw=(json.dumps(proof,sort_keys=True)+'\n').encode();path=Path('/var/lib/b60-inference/evidence')/(a.run_id+'-native-proof.json')
  with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  print(json.dumps({'native_proof_sha256':hashlib.sha256(raw).hexdigest()}),flush=True)
  print(guest(114,'python3','/run/b60-bar-validate-generation.py'),flush=True)
  target='/var/lib/b60-inference/evidence/'+a.run_id+'-native-regression.json'
  print(guest(114,'timeout','180','python3',ROOT+'/runner.py','--endpoint','http://192.168.70.12:11435','--api-key-file','/root/.news-aggregator-llama-key','--cases',ROOT+'/cases.json','--label',a.run_id+'-native','--output',target,'--max-tokens','256','--timeout','60','--fail-fast-runtime',timeout=190,okay=(0,1)),flush=True)
  print(guest(114,'python3','-c','import json,sys; d=json.load(open(sys.argv[1])); assert len(d["results"])==16 and d["pass_count"]>=12; assert all(r["elapsed_seconds"] is not None for r in d["results"]); assert {r["id"] for r in d["results"] if not r["passed"]}<={"stale-news","contradictory-sources","missing-evidence","private-public-join"}; print(json.dumps({"pass_count":d["pass_count"],"total":16,"new_failures":False}))',target),flush=True)
  kernel_gate()
  for fixture in fixtures:workflow(a.run_id,'native-openvino',fixture)
 finally:
  if touched:
   restore_after_trial();recovered=True;CURRENT_UNIT='aster-llama.service'
 if recovered:
  verify.gates()
  for fixture in fixtures:workflow(a.run_id,'sycl-post',fixture)
 print('NATIVE COMPARISON COMPLETE; ACCEPTED SYCL RESTORED',flush=True)
if __name__=='__main__':main()
