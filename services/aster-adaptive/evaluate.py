"""Reproducible offline conformance/microbenchmark; synthetic fixtures only."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path
import pydantic
from baseline import BaselineSelector
from contracts import CONTRACTS, Capability, Catalogue, DecisionRequest, Experiment, HarnessRun, Outcome, validate_proposal

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'services/aster-agent/aster_agent.py'
DEFINITION = HERE / 'experiment-definition.json'
POLICY = hashlib.sha256(b'offline-selection-no-authority-v1').hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def catalogue(selector, allowed=None):
    tree = ast.parse(SOURCE.read_bytes())
    tools = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == 'TOOLS'))
    # Output schemas are opaque because selector-only baseline never runs tools.
    opaque = {'type':'object', 'description':'offline opaque output; no executor binding'}
    return Catalogue(source_digest=selector.digest, capabilities=[Capability(
        capability_id=n, implementation='aster.selector.v1',
        input_schema_digest=digest(tools[n]['function']['parameters']),
        output_schema_digest=digest(opaque), effect='proposal' if n == 'get_arr_repair_proposal' else 'read',
        sensitivity='internal') for n in sorted(selector.names) if allowed is None or n in allowed])


def request(fixture, registry):
    return DecisionRequest(request_id=fixture['id'], content_handle=fixture['id'],
        registry_digest=registry.digest(), policy_digest=POLICY, engine_digest=registry.source_digest,
        sensitivity='internal', deadline_ms=5000)


def run(repeats=100):
    definition = json.loads(DEFINITION.read_text())
    expected_hash = definition['expected_baseline_source_digest']
    selector = BaselineSelector(SOURCE, expected_hash)
    source_hash = selector.digest
    registry = catalogue(selector)
    fixtures = json.loads((HERE/'fixtures.json').read_text())
    baseline_times, adapter_times, outputs = [], [], []
    projections = {}
    for f in fixtures:
        projection = catalogue(selector, frozenset(f.get('allowed', selector.names)))
        projections[projection.digest()] = projection.model_dump()
        req = request(f, projection)
        messages = [{'role':'user','content':f['text']}]
        allowed = frozenset(f.get('allowed', selector.names))
        for _ in range(repeats):
            start=time.perf_counter_ns(); selected=selector.select(messages, set(allowed)); baseline_times.append(time.perf_counter_ns()-start)
            start=time.perf_counter_ns(); decision=selector.propose(req,projection,messages,now=1); validate_proposal(req,decision,projection,now=1); adapter_times.append(time.perf_counter_ns()-start)
        names=[s.capability_id for s in decision.steps]
        assert names == [t['function']['name'] for t in selected] == f['expected_tools'], f['id']
        run_record=HarnessRun(run_id=f['id'],request_id=f['id'],decision_digest=digest(decision.model_dump()),adapter_digest=hashlib.sha256((HERE/'baseline.py').read_bytes()).hexdigest(),duration_ns=adapter_times[-1])
        outcome=Outcome(run_id=f['id'],result='selection_recorded' if names else ('denied' if decision.status == 'deny' else 'abstained'),label_source='synthetic_expectation',route_correct=None)
        outputs.append({'fixture_id':f['id'],'request':req.model_dump(),'selected':names,'decision':decision.model_dump(),'run':run_record.model_dump(),'outcome':outcome.model_dump()})
    def timing(values):
        ordered=sorted(values)
        return {'p50_ns':int(statistics.median(values)),'p95_ns':ordered[int(.95*(len(ordered)-1))]}
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SOURCE,*sorted(HERE.glob('*.py')),HERE/'fixtures.json',DEFINITION,*sorted((ROOT/'schemas/aster').glob('*.json'))]}
    experiment=Experiment(experiment_id='m2-selector-conformance-001',hypothesis='contract-adapter-preserves-baseline-selection',baseline_digest=source_hash,candidate_digest=digest(manifest),dataset_digest=hashlib.sha256((HERE/'fixtures.json').read_bytes()).hexdigest(),evaluator_digest=manifest[str((HERE/'evaluate.py').relative_to(ROOT))],evidence_class='synthetic-conformance-and-local-microbenchmark',state='evaluated',observation_count=len(fixtures))
    return {'experiment':experiment.model_dump(),'trusted_expected_source_digest':expected_hash,'measured_source_digest':source_hash,'environment':{'python':platform.python_version(),'pydantic':pydantic.__version__,'platform':platform.platform()},'fixture_count':len(fixtures),'repeats_per_fixture':repeats,'baseline_selector':timing(baseline_times),'adapter_plus_contract_validation':timing(adapter_times),'manifest':manifest,'catalogue':registry.model_dump(),'eligibility_projections':projections,'results':outputs,'limits':['Tool selection only, not full harness/model latency','Abstention here means no selected tool, not runtime answer refusal','Synthetic expectations are not human gold labels or calibrated accuracy','No model/tool/network execution, permission or deployment']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--schemas',type=Path);args=parser.parse_args()
    if args.schemas:
        args.schemas.mkdir(parents=True,exist_ok=True)
        for cls in CONTRACTS:
            schema=cls.model_json_schema();schema['$schema']='https://json-schema.org/draft/2020-12/schema'
            (args.schemas/(cls.__name__+'.v1.json')).write_text(json.dumps(schema,indent=2)+'\n')
    args.output.write_text(json.dumps(run(),indent=2)+'\n')
