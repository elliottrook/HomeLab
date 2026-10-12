"""Offline capture prototype for Adaptive's public feasibility fixture.

No endpoint, credential reader, CLI model execution or deployment path exists.
Tests inject an in-memory transport. Live use needs a reviewed lab controller.
Returned text is not a validated useful answer; semantic review remains pending.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / 'scripts/aster-adaptive/validate_answer_feasibility.py'
VALIDATOR_SHA = 'a48c028618c3d3f905863b88a3ee838090d9abed938a0279b4c01568c252e3a2'
FIXTURE_SHA = 'b5e7748d5c90a30992cb22dd98aa333b3c7c14ea093a16ea3c29069df5661ef0'


def fixture_cases(raw):
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA:
        raise ValueError('fixture requires reviewed successor pin')
    if hashlib.sha256(VALIDATOR.read_bytes()).hexdigest() != VALIDATOR_SHA:
        raise ValueError('validator requires reviewed successor pin')
    spec = importlib.util.spec_from_file_location('adaptive_answer_fixture', VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate(raw)
    return json.loads(raw)['cases']


def capture(raw, candidate_sha256, session_id, transport, clock, egress='local'):
    if (not re.fullmatch('[0-9a-f]{64}', candidate_sha256) or
            not re.fullmatch('[a-z0-9-]{1,64}', session_id) or egress != 'local'):
        raise ValueError('invalid or nonlocal development profile')
    records = []
    for case in fixture_cases(raw):
        # Rubrics and prohibited claims are NEVER included in backend requests.
        request = {k: case[k] for k in ('request', 'clock', 'context', 'privacy')}
        started = clock()
        answer_hash = None
        try:
            answer = transport(request)
            if not isinstance(answer, str) or not answer.strip():
                outcome = 'invalid_response'
            else:
                outcome = 'returned_unscored'
                answer_hash = hashlib.sha256(answer.encode()).hexdigest()
        except TimeoutError:
            outcome = 'timeout'
        except Exception:
            # No exception text or hidden reasoning is exported.
            outcome = 'transport_error'
        elapsed = clock() - started
        if type(elapsed) not in (float, int) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('invalid elapsed time')
        records.append({'case_id': case['id'], 'class': case['class'],
                        'elapsed_seconds': elapsed, 'outcome': outcome,
                        'answer_sha256': answer_hash})
    return {'schema': 'b60-answer-development-capture.v0', 'fixture_sha256': FIXTURE_SHA,
            'candidate_sha256': candidate_sha256, 'session_id': session_id,
            'egress': 'local', 'tool_execution': 'disabled', 'records': records,
            'quality': 'unscored', 'qualification_eligible': False}


def summarize(raw, packet):
    cases = fixture_cases(raw)
    if (set(packet) != {'schema', 'fixture_sha256', 'candidate_sha256', 'session_id',
            'egress', 'tool_execution', 'records', 'quality', 'qualification_eligible'} or
            packet['schema'] != 'b60-answer-development-capture.v0' or
            packet['fixture_sha256'] != FIXTURE_SHA or packet['egress'] != 'local' or
            packet['tool_execution'] != 'disabled' or packet['quality'] != 'unscored' or
            packet['qualification_eligible'] is not False):
        raise ValueError('changed capture scope')
    if (not re.fullmatch('[0-9a-f]{64}', packet['candidate_sha256']) or
            not re.fullmatch('[a-z0-9-]{1,64}', packet['session_id'])):
        raise ValueError('invalid profile/session identity')
    expected = {c['id']: c['class'] for c in cases}
    seen, times = set(), []
    counts = {k: 0 for k in ('returned_unscored', 'timeout', 'transport_error', 'invalid_response')}
    for row in packet['records']:
        if (set(row) != {'case_id', 'class', 'elapsed_seconds', 'outcome', 'answer_sha256'} or
                row['case_id'] in seen or expected.get(row['case_id']) != row['class'] or
                row['outcome'] not in counts):
            raise ValueError('unknown, duplicate or changed case')
        elapsed = row['elapsed_seconds']
        if type(elapsed) not in (float, int) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('invalid elapsed time')
        returned = row['outcome'] == 'returned_unscored'
        if ((returned and (not isinstance(row['answer_sha256'], str) or
                not re.fullmatch('[0-9a-f]{64}', row['answer_sha256']))) or
                (not returned and row['answer_sha256'] is not None)):
            raise ValueError('invalid answer digest')
        seen.add(row['case_id'])
        counts[row['outcome']] += 1
        times.append(elapsed)
    if seen != set(expected):
        raise ValueError('missing attempts; cannot omit failed cases')
    ordered = sorted(times)
    return {'attempts': len(times), 'outcomes': counts,
            'terminal_observed_p50_seconds': statistics.median(times),
            'terminal_observed_p95_seconds': ordered[math.ceil(.95 * len(times)) - 1],
            'censored_timeout_count': counts['timeout'],
            'complete_useful_answer_p50_seconds': None,
            'complete_useful_answer_p95_seconds': None,
            'qualification_eligible': False,
            'limits': ['Terminal timing includes ALL attempts, not useful-answer latency',
                       'Semantic review and independent qualification remain pending',
                       'Timeout time is a censored lower bound, not completed-answer time']}
