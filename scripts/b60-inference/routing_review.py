"""Pinned Adaptive routing-scorer adapter: development evidence, never qualification."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

SCORER = Path(__file__).resolve().parents[1] / 'aster-adaptive/ask_route_benchmark.py'
PIN = 'fec2ff451529be1e9855ccffc5e6083382b7b09608a266597ed5e85f8652bfd4'
FIXTURE = 'c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec'


def review(fixture, run, manifest, expected_scorer=PIN):
    if hashlib.sha256(SCORER.read_bytes()).hexdigest() != expected_scorer:
        raise ValueError('scorer drift')
    if hashlib.sha256(fixture).hexdigest() != FIXTURE:
        raise ValueError('fixture requires a new reviewed version')
    spec = importlib.util.spec_from_file_location('adaptive_route_review', SCORER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    score = module.score(fixture, run, manifest)
    return {'schema': 'b60-routing-development-review.v1',
            'scorer_sha256': expected_scorer, 'fixture_sha256': FIXTURE,
            'run_sha256': hashlib.sha256(run).hexdigest(),
            'manifest_sha256': hashlib.sha256(json.dumps(manifest, sort_keys=True,
                separators=(',', ':'), allow_nan=False).encode()).hexdigest(),
            'valid': score['valid'], 'total': score['total_cases'],
            'exact_agreement': score['exact_agreement'],
            'by_family': score['by_family'],
            'route_request_p50_seconds': score['request_latency_p50_seconds'],
            'route_request_p95_seconds': score['request_latency_p95_seconds'],
            'qualification_eligible': False, 'deployment_authorized': False,
            'limits': ['Exposed development routing set, not answer quality',
                       'Single serial observations do not establish population p95',
                       'No policy, tool or production-routing grant']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('fixture', 'run', 'manifest'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        result = review(args.fixture.read_bytes(), args.run.read_bytes(),
                        json.loads(args.manifest.read_text()))
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({'decision': 'hold', 'qualification_eligible': False,
                          'reason': 'invalid or drifted routing packet'}))
        return 1
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
