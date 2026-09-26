"""One fresh four-case lineage exercise, not a comparative performance experiment."""
import argparse
import asyncio
import hashlib
import json
import socket
import tempfile
from pathlib import Path
from unittest.mock import patch

from contracts import HarnessRun
from evidence_store import Dataset, EvidenceStore, digest
from fixtures import CASES, make_run
from offline_baseline import FixtureAdapter


def source_digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


async def measure(root):
    script_root = Path(__file__).parent
    sources = {name:source_digest(script_root/name) for name in (
        'measure_lineage.py', 'offline_baseline.py', 'contracts.py', 'fixtures.py', 'evidence_store.py')}
    adapter = FixtureAdapter()
    dataset = Dataset(dataset_id='m4-lineage-four-cases', cases=tuple(dict(
        case_id=name, family_id=name, input_digest=digest(prompt),
        expected_digest=digest({'status':'completed','tool_calls':len(ids)}))
        for name,prompt,ids in CASES)).model_dump(mode='json')
    experiment_id = 'm4-lineage-001'
    store = EvidenceStore(root/'measurement.db')
    try:
        store.append('dataset', 'dataset', dataset)
        # Freeze all artifacts before executing any fixture. HarnessRun binds the
        # extracted Aster source; evaluator digest additionally binds the wrapper.
        store.append('spec', 'experiment', dict(experiment_id=experiment_id, owner='fixture-proposer',
            baseline_digest=adapter.source_digest, candidate_digest=adapter.source_digest,
            evaluator_digest=digest(sources), dataset_digest=digest(dataset),
            status='preregistered', metric='offline-payload-construction-ms'))
        before = store.verify()
        passed = 0
        for name,prompt,ids in CASES:
            run_data = make_run(adapter.source_digest,ids).model_dump(mode='json')
            run_data.update(run_id='lineage-'+name, experiment_id=experiment_id)
            run = HarnessRun.model_validate_json(json.dumps(run_data))
            run_head = store.append('run-'+name, 'run', dict(dataset_digest=digest(dataset),
                case_id=name, candidate_role='candidate', run=run.model_dump(mode='json')))
            outcome = await adapter.run(run,prompt,now=1000)
            store.append('outcome-'+name, 'linked-outcome', dict(experiment_id=experiment_id,
                run_event_digest=run_head, outcome=outcome.model_dump(mode='json')))
            passed += outcome.status=='completed' and outcome.tool_calls==len(ids)
        head = store.verify()
        backup_head = store.backup(root/'restore.db')
        restored = EvidenceStore(root/'restore.db')
        try:
            restored.verify(expected_head=head)
        finally:
            restored.close()
        return dict(schema_version='lineage-proof.v1', data_class='synthetic',
            experiment_id=experiment_id, implementation_digests=sources,
            preregistered_head=before, final_head=head, backup_head=backup_head,
            restore_verified=True, cases_passed=passed, case_count=len(CASES),
            events=store.records(), limits=[
                'Four previously authored fixtures, not independent representative quality labels',
                'One observation per case; elapsed times are not a performance comparison',
                'No paired baseline, aggregate evaluation or authenticated review recorded',
                'Source digests bind content, not the authenticity of asserted measurements',
                'No model requests, production readers or broker access'])
    finally:
        store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    # Reserve a new artifact path; never overwrite prior evidence.
    with args.output.open('x') as output:
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(socket.socket,'connect',side_effect=AssertionError('network forbidden')), \
                 patch.object(socket.socket,'connect_ex',side_effect=AssertionError('network forbidden')):
                result = asyncio.run(measure(Path(directory)))
        json.dump(result,output,indent=2)
        output.write('\n')
    print(json.dumps({key:result[key] for key in ('case_count','cases_passed','restore_verified')}))


if __name__=='__main__':
    main()
