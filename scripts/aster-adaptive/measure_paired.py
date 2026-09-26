"""Fresh paired source-slice exercise with outcome-bound evaluation."""
import argparse
import asyncio
import json
import socket
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from contracts import HarnessRun, Outcome
from evidence_store import Dataset, EvidenceStore, digest
from fixtures import CASES, make_run
from measure_lineage import source_digest
from offline_baseline import FixtureAdapter, FixtureRequest
from paired_evidence import aggregate


async def measure(root):
    scripts = Path(__file__).parent
    sources = {name:source_digest(scripts/name) for name in (
        'measure_paired.py','measure_lineage.py','offline_baseline.py','contracts.py',
        'fixtures.py','evidence_store.py','paired_evidence.py')}
    adapter, baseline = FixtureAdapter(), FixtureAdapter()
    dataset = Dataset(dataset_id='m4-paired-four-cases',cases=tuple(dict(
        case_id=name,family_id=name,input_digest=digest(prompt),
        expected_digest=digest({'status':'completed','tool_calls':len(ids)}))
        for name,prompt,ids in CASES)).model_dump(mode='json')
    experiment_id = 'm4-paired-001'
    store = EvidenceStore(root/'paired.db')
    try:
        store.append('dataset','dataset',dataset)
        store.append('spec','experiment',dict(experiment_id=experiment_id,owner='fixture-proposer',
            baseline_digest=adapter.source_digest,candidate_digest=adapter.source_digest,
            evaluator_digest=digest(sources),dataset_digest=digest(dataset),
            status='preregistered',metric='offline-payload-construction-ms'))
        plan = dict(experiment_id=experiment_id,repetitions=10,warmups=2,maximum_p95_delta_ms=5.0)
        plan_head = store.append('plan','paired-plan',plan)
        pairs = []
        for name,prompt,ids in CASES:
            allowed = {c.implementation for c in make_run(adapter.source_digest,ids).projection.capabilities}
            calls = 0
            async def execute(tool,arguments):
                nonlocal calls
                if tool not in allowed:
                    raise AssertionError('unprojected fixture tool')
                calls += 1
                return {'fixture':True,'status':'available'}
            baseline.namespace['execute_tool'] = execute
            for i in range(-plan['warmups'],plan['repetitions']):
                pair = dict(case_id=name,repetition=i)
                for role in (('baseline','candidate') if i%2==0 else ('candidate','baseline')):
                    data = make_run(adapter.source_digest,ids).model_dump(mode='json')
                    data.update(run_id=f'{name}-{role}-{i}',experiment_id=experiment_id)
                    run = HarnessRun.model_validate_json(json.dumps(data))
                    if i>=0:
                        h = store.append('run-'+run.run_id,'run',dict(dataset_digest=digest(dataset),
                            case_id=name,candidate_role=role,run=data))
                    calls = 0
                    started = time.perf_counter()
                    if role=='candidate':
                        out = await adapter.run(run,prompt,now=1000)
                    else:
                        payload = await baseline.namespace['build_payload'](
                            FixtureRequest(prompt),{'identity':'Offline synthetic fixture'},allowed)
                        size = len(json.dumps(payload,sort_keys=True,separators=(',',':')).encode())
                        out = Outcome(run_id=run.run_id,status='completed',verification='fixture-conformance',
                                      tool_calls=calls,elapsed_ms=0.0,output_bytes=size)
                    elapsed = (time.perf_counter()-started)*1000
                    if i>=0:
                        measured = out.model_dump(mode='json') | {'elapsed_ms':elapsed}
                        pair[role+'_outcome'] = store.append('out-'+run.run_id,'linked-outcome',dict(
                            experiment_id=experiment_id,run_event_digest=h,outcome=measured))
                if i>=0:
                    pairs.append(pair)
        evaluation = dict(experiment_id=experiment_id,plan_event_digest=plan_head,pairs=pairs)
        totals, details = aggregate(evaluation,store.records(),digest)
        store.append('evaluation','paired-evaluation',evaluation | totals)
        head = store.verify()
        backup_head = store.backup(root/'backup.db')
        restored = EvidenceStore(root/'backup.db')
        try:
            restored.verify(expected_head=head)
        finally:
            restored.close()
        return dict(schema_version='paired-proof.v1',data_class='synthetic',implementation_digests=sources,
            protocol_head=plan_head,final_head=head,backup_head=backup_head,restore_verified=True,
            totals=totals,case_details=details,events=store.records(),limits=[
                'Four authored synthetic families; repetitions are not independent quality examples',
                'Controlled source-slice overhead only; no model or production traffic',
                'SQLite registration/aggregation and source loading excluded from timing',
                'Both timers include payload construction, serialization and Outcome construction',
                'Content hashes and asserted outcomes do not authenticate the measuring process',
                'No authenticated reviewer decision or adoption claim'])
    finally:
        store.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    with args.output.open('x') as output:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
                 patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
                result=asyncio.run(measure(Path(directory)))
        json.dump(result,output,indent=2)
        output.write('\n')
    print(json.dumps({'totals':result['totals'],'case_details':result['case_details'],
                      'restore_verified':result['restore_verified']}))


if __name__=='__main__':
    main()
