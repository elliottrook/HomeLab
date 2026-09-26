"""Reproducible offline benchmark and schema export, fixed synthetic inputs only."""
import argparse
import asyncio
import json
import math
import platform
import resource
import socket
import statistics
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pydantic
from contracts import Capability, Decision, Experiment, HarnessRun, Outcome, Projection
from fixtures import CASES, CATALOGUE, INPUT_SCHEMA, OUTPUT_SCHEMA, content_digest, make_run
from offline_baseline import FixtureAdapter, FixtureRequest, digest


def summarize(values):
    ordered = sorted(values)
    return {'samples': len(values), 'p50_ms': statistics.median(values),
            'p95_ms': ordered[math.ceil(.95 * len(ordered)) - 1]}


async def measure():
    adapter = FixtureAdapter()
    records = []
    for name, prompt, ids in CASES:
        run = make_run(adapter.source_digest, ids)
        allowed = {c.implementation for c in run.projection.capabilities}
        async def fixture_execute(name, arguments):
            if name not in allowed:
                raise AssertionError('unprojected tool')
            return {'fixture': True, 'status': 'available'}
        baseline = FixtureAdapter()
        baseline.namespace['execute_tool'] = fixture_execute
        direct, adapted = [], []
        cpu_start = time.process_time()
        last = None
        # Alternate order to reduce systematic warm/order bias; discard 10 warmups.
        for iteration in range(210):
            async def bare():
                started = time.perf_counter()
                payload = await baseline.namespace['build_payload'](
                    FixtureRequest(prompt), {'identity': 'Offline synthetic fixture'}, allowed)
                json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
                return (time.perf_counter() - started) * 1000
            async def wrapped():
                started = time.perf_counter()
                result = await adapter.run(run, prompt, now=1000)
                elapsed = (time.perf_counter() - started) * 1000
                if result.status != 'completed' or result.tool_calls != len(ids):
                    raise AssertionError('fixture conformance failed')
                return elapsed, result
            if iteration % 2:
                a, last = await wrapped()
                b = await bare()
            else:
                b = await bare()
                a, last = await wrapped()
            if iteration >= 10:
                direct.append(b)
                adapted.append(a)
        records.append({'case_id': name, 'direct_slice': summarize(direct),
                        'validated_adapter': summarize(adapted),
                        'process_cpu_ms_including_warmup': (time.process_time()-cpu_start)*1000,
                        'payload_bytes': last.output_bytes, 'tool_calls': last.tool_calls,
                        'model_calls': 0, 'prompt_tokens': None, 'answer_quality': 'not-evaluated'})
    cold = []
    for _ in range(20):
        start = time.perf_counter()
        FixtureAdapter()
        cold.append((time.perf_counter()-start)*1000)
    return {'schema_version': 'baseline-evidence.v1', 'scope': 'synthetic-source-slice-only',
            'aster_source_digest': adapter.source_digest,
            'dataset_digest': content_digest(CASES), 'python': platform.python_version(),
            'pydantic': pydantic.__version__, 'platform': platform.platform(),
            'source_slice_load': summarize(cold), 'cases': records,
            'peak_process_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
                                      (1 if sys.platform == 'darwin' else 1024),
            'limits': ['No model, provider, production reader or broker execution',
                       'RSS is process high-water mark, not incremental adapter memory',
                       'No tokenizer: bytes are not prompt tokens',
                       'Source-slice loading excludes full app startup and imported runtime modules',
                       'Constants use documented fixture overrides, not verified live configuration',
                       'Timing is descriptive, not a preregistered adoption threshold']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('network forbidden')):
        results = asyncio.run(measure())
    for model in (Capability, Projection, Decision, HarnessRun, Outcome, Experiment):
        (args.output / (model.__name__.lower()+'.schema.json')).write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True)+'\n')
    (args.output / 'fixture-input.schema.json').write_text(json.dumps(INPUT_SCHEMA, indent=2)+'\n')
    (args.output / 'fixture-output.schema.json').write_text(json.dumps(OUTPUT_SCHEMA, indent=2)+'\n')
    (args.output / 'catalogue.json').write_text(json.dumps([c.model_dump(mode='json') for c in CATALOGUE], indent=2)+'\n')
    experiment = Experiment(experiment_id='m2-baseline', owner='fixture-owner',
                            baseline_digest=results['aster_source_digest'],
                            candidate_digest=digest(Path(__file__).with_name('offline_baseline.py').read_bytes()),
                            evaluator_digest=digest(Path(__file__).read_bytes()),
                            dataset_digest=results['dataset_digest'], status='measured',
                            metric='offline-payload-construction-ms')
    (args.output / 'experiment.json').write_text(experiment.model_dump_json(indent=2)+'\n')
    results['implementation_sha256'] = {p.name: digest(p.read_bytes()) for p in sorted(Path(__file__).parent.glob('*.py'))}
    (args.output / 'baseline.json').write_text(json.dumps(results, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'cases': len(results['cases']), 'samples_per_case': 200,
                      'output': str(args.output), 'scope': results['scope']}))


if __name__ == '__main__':
    main()
