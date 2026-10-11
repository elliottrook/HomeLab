#!/usr/bin/env python3
"""Create-once comparison of matched grounded/8K measurements, never missing runs."""
import argparse
import hashlib
import json
import os
import re
import statistics
from pathlib import Path

FIXTURES=['aster-grounded-retrieval','aster-context-8k']
def summarize(root,prefix):
    report={'complete':True,'evidence_sha256':{},'fixtures':{},
            'limitations':['Synthetic grounding and marker recall, not arbitrary household correctness.',
                           'Request latency and server decode rate are distinct measures.',
                           'Compare only identical prompt hashes and calibrated token counts.']}
    for fixture in FIXTURES:
        groups={}
        prompts=set()
        for phase in ['vulkan-pre','sycl','vulkan-post']:
            path=root/f'{prefix}-{phase}-{fixture}.json'
            if not path.exists():
                report['complete']=False
                continue
            raw=path.read_bytes()
            report['evidence_sha256'][path.name]=hashlib.sha256(raw).hexdigest()
            data=json.loads(raw)
            samples=data['samples']
            assert data['fixture']==fixture and data['health_passed'] and len(samples)==12
            assert all(s['correct'] for s in samples), 'correctness regression'
            prompts.add(data['prompt_sha256'])
            measured=[s for s in samples if s['phase']=='decode' and s['control_role']=='measured']
            assert len(measured)==5 and all(s['seconds']>0 and s['tokens']>0 for s in measured)
            groups[phase]={'request_seconds':[s['seconds'] for s in measured],
                           'completion_tokens':[s['tokens'] for s in measured],
                           'decode_tokens_per_second':[s['tokens_per_second'] for s in measured],
                           'rate_sources':sorted({s['rate_source'] for s in measured}),
                           'prompt_tokens':sorted({s['tokens'] for s in samples if s['phase']=='prefill'})}
        if len(groups)!=3:
            continue
        assert len(prompts)==1, 'different calibrated prompts'
        assert groups['vulkan-pre']['prompt_tokens']==groups['sycl']['prompt_tokens']==groups['vulkan-post']['prompt_tokens']
        target=8000 if fixture=='aster-context-8k' else 2048
        assert groups['sycl']['prompt_tokens'] and all(target<=n<target+128 for n in groups['sycl']['prompt_tokens']), 'context coverage not proven'
        controls=groups['vulkan-pre']['request_seconds']+groups['vulkan-post']['request_seconds']
        candidate=groups['sycl']['request_seconds']
        result={'phases':groups,'request_latency_reduction_percent':100*(1-statistics.median(candidate)/statistics.median(controls))}
        if all(g['rate_sources']==['server_predicted_per_second'] for g in groups.values()):
            baseline=groups['vulkan-pre']['decode_tokens_per_second']+groups['vulkan-post']['decode_tokens_per_second']
            result['server_decode_improvement_percent']=100*(statistics.median(groups['sycl']['decode_tokens_per_second'])/statistics.median(baseline)-1)
        report['fixtures'][fixture]=result
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    parser.add_argument('--evidence-root',type=Path,default=Path('/var/lib/b60-inference/evidence'))
    parser.add_argument('--write-report',action='store_true')
    args=parser.parse_args()
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',args.run_id)
    prefix='matched-sycl-exclusive-'+args.run_id
    report=summarize(args.evidence_root,prefix)
    raw=(json.dumps(report,sort_keys=True)+'\n').encode()
    if args.write_report:
        assert report['complete'], 'incomplete comparison'
        path=args.evidence_root/(prefix+'-workflow-report.json')
        with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
    print(raw.decode(),end='')
if __name__=='__main__': main()
