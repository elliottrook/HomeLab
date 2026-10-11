#!/usr/bin/env python3
"""Create-once native deployment comparison; metric/quant/cache caveats explicit."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import statistics

FIXTURES=['b60-tg128-cold','aster-grounded-retrieval','aster-context-8k']
def summarize(root,prefix):
 report={'complete':True,'fixtures':{},'evidence_sha256':{},'limitations':[
  'GGUF Q4_K_M versus vendor INT4_ASYM group128: runtime and quantization both change.',
  'Native PerfMetrics throughput and llama.cpp predicted rate have different implementations; do not claim a backend-only decode percentage.',
  'OpenVINO prefix cache disabled; SYCL follows each fixture cache policy.',
  'Only equal-length output with identical calibrated input supports a matched request-latency claim.',
  'Synthetic API adapter is not a permanent serving stack and does not prove streaming/tools/media compatibility.']}
 for fixture in FIXTURES:
  phases={};prompts=set()
  for phase in ['sycl-pre','native-openvino','sycl-post']:
   path=root/f'{prefix}-{phase}-{fixture}.json'
   if not path.exists():report['complete']=False;continue
   raw=path.read_bytes();d=json.loads(raw);report['evidence_sha256'][path.name]=hashlib.sha256(raw).hexdigest()
   assert d['fixture']==fixture and d['health_passed'] and len(d['samples'])==12 and all(s['correct'] for s in d['samples'])
   prompts.add(d['prompt_sha256']);s=[s for s in d['samples'] if s['phase']=='decode' and s['control_role']=='measured']
   assert len(s)==5 and all(r['seconds']>0 and r['tokens']>0 for r in s)
   if fixture=='b60-tg128-cold':
    assert d.get('generation_policy')=={'ignore_eos':True,'max_output_tokens':128}
    assert all(r['tokens']==128 for r in s)
   phases[phase]={'request_seconds':[r['seconds'] for r in s],'output_tokens':[r['tokens'] for r in s],'reported_decode_tps':[r['tokens_per_second'] for r in s],'input_tokens':sorted({r['tokens'] for r in d['samples'] if r['phase']=='prefill'})}
  if len(phases)!=3:continue
  target=64 if fixture=='b60-tg128-cold' else 2048 if fixture=='aster-grounded-retrieval' else 8000
  assert all(g['input_tokens'] and all(target<=t<target+128 for t in g['input_tokens']) for g in phases.values())
  controls=phases['sycl-pre']['request_seconds']+phases['sycl-post']['request_seconds'];candidate=phases['native-openvino']['request_seconds']
  equal=len(set(t for g in phases.values() for t in g['output_tokens']))==1
  result={'phases':phases,'identical_calibrated_prompt':len(prompts)==1,'identical_output_length':equal,
          'observed_request_latency_reduction_percent':100*(1-statistics.median(candidate)/statistics.median(controls)),
          'matched_latency_claim_supported':len(prompts)==1 and equal}
  report['fixtures'][fixture]=result
 return report
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-id',required=True);p.add_argument('--root',type=Path,default=Path('/var/lib/b60-inference/evidence'));p.add_argument('--write-report',action='store_true');a=p.parse_args()
 assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,50}',a.run_id)
 report=summarize(a.root,a.run_id);raw=(json.dumps(report,sort_keys=True)+'\n').encode()
 if a.write_report:
  assert report['complete'] and len(report['fixtures'])==3
  path=a.root/(a.run_id+'-native-report.json')
  with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 print(raw.decode(),end='')
if __name__=='__main__':main()
