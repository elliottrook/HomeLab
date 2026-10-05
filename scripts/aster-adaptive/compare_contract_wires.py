"""Compare trusted pinned selector contracts with fixture-harness contracts.

No conversion is performed. Never use schema_version alone to select a validator.
"""
import argparse
import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path
from unittest.mock import patch

import contracts as harness
from fixtures import CATALOGUE, make_run

SELECTOR_COMMIT='1a8fa680908eac8e0b7bb76845a0b1b061e593d7'
PINS={'contracts.py':'78e78137d3fb67de4f8fd2a4634728d5a9a0e4ad07fa86c719556dbd1a074a4e',
      'conformance-vectors.json':'18d6dddb66b56a200d0ede7bd7cd1e9ca310caac895f3b56cf56f47916217465'}


def compare(selector_dir):
    for name,expected in PINS.items():
        if hashlib.sha256((selector_dir/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('selector snapshot differs from reviewed pin')
    spec=importlib.util.spec_from_file_location('selector_wire_candidate',selector_dir/'contracts.py')
    selector=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=selector
    spec.loader.exec_module(selector)
    corpus=json.loads((selector_dir/'conformance-vectors.json').read_text())
    selected={v['contract']:v['input'] for v in corpus['vectors'] if v['scope']=='structural' and v['accept']}
    d='sha256:'+'1'*64
    run=make_run(d)
    samples={
        'Capability':CATALOGUE[0], 'Decision':run.decision, 'HarnessRun':run,
        'Outcome':harness.Outcome(run_id=run.run_id,status='completed',verification='fixture-conformance',
                                  tool_calls=1,elapsed_ms=1.0,output_bytes=100),
        'Experiment':harness.Experiment(experiment_id='mapping-only',owner='fixture',baseline_digest=d,
            candidate_digest=d,dataset_digest=d,evaluator_digest=d,status='preregistered',
            metric='offline-payload-construction-ms')}
    results=[]
    for name,model in samples.items():
        a=model.model_dump(mode='json'); b=selected[name]
        for source,payload,own,other in (('harness',a,harness,selector),('selector',b,selector,harness)):
            encoded=json.dumps(payload)
            getattr(own,name).model_validate_json(encoded)
            try:
                getattr(other,name).model_validate_json(encoded)
            except ValueError:
                accepted=False
            else:
                accepted=True
            results.append(dict(contract=name,source=source,self_accept=True,other_accept=accepted,
                                schema_version=payload['schema_version']))
    assert all(not row['other_accept'] for row in results), 'unexpected cross-profile acceptance'
    return dict(schema_version='contract-wire-comparison.v1',selector_commit=SELECTOR_COMMIT,
        selector_pins=PINS,harness_contract_digest=hashlib.sha256(Path(harness.__file__).read_bytes()).hexdigest(),
        results=results,shared_version_collisions=[n for n,m in samples.items()
            if m.schema_version==selected[n]['schema_version']],
        scope='ten structural sample checks; not general semantic equivalence or a migration',
        conclusion='distinct incompatible profiles; no automatic conversion or authority')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--selector-dir',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
         patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
        result=compare(args.selector_dir)
    with args.output.open('x') as output:
        json.dump(result,output,indent=2); output.write('\n')
    print(json.dumps({'self_accepted':len(result['results']),'cross_rejected':sum(not r['other_accept'] for r in result['results']),
                      'shared_version_collisions':result['shared_version_collisions']}))
