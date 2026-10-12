"""Offline bridge to Adaptive-owned capture/review v0; no production qualification.

Requires original synthetic attempts and digest-bound review. Never reconstructs
answers or phase timings from B60's earlier hash-only capture prototype.
"""
import hashlib
import importlib
import json
import math
from pathlib import Path
import statistics
import sys

ADAPTIVE = Path(__file__).resolve().parents[1] / 'aster-adaptive'
PINS = {
    'validate_answer_feasibility': 'a48c028618c3d3f905863b88a3ee838090d9abed938a0279b4c01568c252e3a2',
    'capture_answer_feasibility': 'c0458afdbbd3ffae3473b3850799eccd1436637ac70a9a0a465d05d85b1e1d9f',
    'score_answer_feasibility': 'c1fd4b982eab2b5066355d5952cb05b346850d0a3b265d7206bdcda83e0d9d46',
}
FIXTURE_SHA = 'b5e7748d5c90a30992cb22dd98aa333b3c7c14ea093a16ea3c29069df5661ef0'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def modules(fixture_raw):
    if sha(fixture_raw) != FIXTURE_SHA:
        raise ValueError('fixture drift')
    for name, pin in PINS.items():
        if sha((ADAPTIVE / (name + '.py')).read_bytes()) != pin:
            raise ValueError('Adaptive source drift')
    sys.path.insert(0, str(ADAPTIVE))
    try:
        loaded = {name: importlib.import_module(name) for name in PINS}
    finally:
        sys.path.pop(0)
    for name, module in loaded.items():
        if Path(module.__file__).resolve() != (ADAPTIVE / (name + '.py')).resolve():
            raise ValueError('wrong loaded Adaptive module')
    return loaded


def project_attempts(fixture_raw, attempts_raw):
    owned = modules(fixture_raw)
    return encoded(owned['capture_answer_feasibility'].capture(fixture_raw, attempts_raw))


def review(fixture_raw, attempts_raw, capture_raw, review_raw):
    owned = modules(fixture_raw)
    expected = owned['capture_answer_feasibility'].capture(fixture_raw, attempts_raw)
    captured = json.loads(capture_raw)
    if encoded(captured) != encoded(expected):
        raise ValueError('capture does not reproduce source attempts')
    scored = owned['score_answer_feasibility'].score(fixture_raw, capture_raw, review_raw)
    scores = {row['case_id']: row for row in scored['cases']}
    buckets = {}
    for row in captured['attempts']:
        bucket = buckets.setdefault(row['class'], {'samples': 0, 'review_label_passed': 0,
            'boundary_violations': 0, 'failed_attempts': 0, 'censored_timeouts': 0,
            'terminal_times': []})
        label = scores[row['case_id']]
        bucket['samples'] += 1
        bucket['review_label_passed'] += int(label['passed'])
        bucket['boundary_violations'] += int(label['boundary_violation'])
        bucket['failed_attempts'] += int(row['status'] == 'failed')
        bucket['censored_timeouts'] += int(row['error_code'] == 'timeout')
        bucket['terminal_times'].append(row['total_ms'] / 1000)
    for bucket in buckets.values():
        times = sorted(bucket.pop('terminal_times'))
        bucket['terminal_observed_p50_seconds'] = statistics.median(times)
        bucket['terminal_observed_p95_seconds'] = times[math.ceil(.95 * len(times))-1]
        # Refuse optimistic completion percentiles that silently omit failures.
        complete = bucket['review_label_passed'] == bucket['samples']
        bucket['label_passed_completion_p50_seconds'] = statistics.median(times) if complete else None
        bucket['label_passed_completion_p95_seconds'] = times[math.ceil(.95 * len(times))-1] if complete else None
    return {'schema': 'b60-adaptive-answer-review.v0',
            'fixture_sha256': FIXTURE_SHA, 'attempts_sha256': sha(attempts_raw),
            'capture_sha256': sha(capture_raw), 'review_sha256': sha(review_raw),
            'candidate_profile_sha256': captured['candidate_profile_sha256'],
            'adaptive_source_pins': PINS.copy(), 'classes': buckets,
            'qualification_eligible': False, 'release_gate_input_eligible': False,
            'deployment_authorized': False, 'review_independence': 'unverified',
            'limits': ['Provided review labels are not independently verified human judgments',
                       'Public six-case development set is not a held-out task bar',
                       'Terminal timing includes failures; timeouts are censored',
                       'Per-class percentiles are descriptive, not stable population p95',
                       'Runtime provenance, policy floors and latency budgets remain pending']}
