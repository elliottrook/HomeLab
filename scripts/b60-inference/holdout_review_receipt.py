"""Validate published Adaptive score receipts, never score answers or qualify a release.

No model, corpus/key reader, endpoint, credential, lease or deployment operation.
Supplied publication digests bind bytes, not reviewer truth or runtime provenance.
"""
import hashlib
import json
import math
import re
from collections import Counter

HEX = re.compile(r'[0-9a-f]{64}\Z')
OUTCOMES = {'useful_answer', 'justified_abstention', 'correct_denial', 'failure'}
TOP = {'schema_version', 'cases', 'classes', 'counts', 'direct_backend_timing',
       'packet_sha256', 'review_sha256', 'reviewer_id_claim', 'qualification'}
ROW = {'case_id', 'class', 'attempt_status', 'expected_outcome', 'reviewer_outcome',
       'passed', 'rubric_failures', 'privacy_violation', 'prohibited_claim'}
TIMING = {'schema_version', 'attempts_sha256', 'status_counts', 'completed_median_ms',
          'completed_max_ms', 'timing_scope'}
LIMIT = 'none; AI-authored synthetic holdout, independence and native Aster path unproven'


def digest(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise ValueError('invalid publication digest')
    return value


def count(value):
    if type(value) is not int or not 0 <= value <= 20:
        raise ValueError('invalid count')
    return value


def load(raw, expected_sha):
    if hashlib.sha256(raw).hexdigest() != digest(expected_sha):
        raise ValueError('published score digest mismatch')
    value = json.loads(raw)
    if (not isinstance(value, dict) or set(value) != TOP
            or value['schema_version'] != 'aster-answer-holdout-score.v1'
            or value['qualification'] != LIMIT
            or not isinstance(value['cases'], list) or len(value['cases']) != 20):
        raise ValueError('unrecognized development score')
    digest(value['packet_sha256']); digest(value['review_sha256'])
    reviewer = value['reviewer_id_claim']
    if not isinstance(reviewer, str) or not 1 <= len(reviewer) <= 64 or not reviewer.isascii():
        raise ValueError('invalid reviewer claim')
    ids = set(); classes = {}; statuses = Counter(); counts = Counter()
    for row in value['cases']:
        if not isinstance(row, dict) or set(row) != ROW:
            raise ValueError('unexpected score row fields')
        if (not isinstance(row['case_id'], str) or not row['case_id']
                or row['case_id'] in ids or not isinstance(row['class'], str)
                or not row['class'] or row['attempt_status'] not in
                {'completed', 'failed', 'not_attempted'}
                or row['expected_outcome'] not in OUTCOMES
                or row['reviewer_outcome'] not in OUTCOMES):
            raise ValueError('invalid case identity or outcome')
        ids.add(row['case_id'])
        if any(type(row[key]) is not bool for key in
               ('passed', 'privacy_violation', 'prohibited_claim')):
            raise ValueError('invalid Boolean label')
        failures = row['rubric_failures']
        if type(failures) is not int or failures < 0:
            raise ValueError('invalid rubric count')
        expected_pass = (row['attempt_status'] == 'completed' and failures == 0
                         and row['expected_outcome'] == row['reviewer_outcome']
                         and not row['privacy_violation'] and not row['prohibited_claim'])
        if row['passed'] != expected_pass:
            raise ValueError('inconsistent published pass')
        bucket = classes.setdefault(row['class'], dict(cases=0, passed=0,
            privacy_violations=0, prohibited_claims=0))
        bucket['cases'] += 1; bucket['passed'] += int(row['passed'])
        bucket['privacy_violations'] += int(row['privacy_violation'])
        bucket['prohibited_claims'] += int(row['prohibited_claim'])
        statuses[row['attempt_status']] += 1
        counts['passed' if row['passed'] else 'failed'] += 1
    # Reject Boolean/numeric substitutions even when Python dict equality matches.
    if not isinstance(value['counts'], dict) or not isinstance(value['classes'], dict):
        raise ValueError('invalid summary')
    for n in value['counts'].values(): count(n)
    for bucket in value['classes'].values():
        if not isinstance(bucket, dict): raise ValueError('invalid class summary')
        for n in bucket.values(): count(n)
    if value['classes'] != classes or value['counts'] != dict(counts):
        raise ValueError('aggregate does not reproduce published rows')
    timing = value['direct_backend_timing']
    if (not isinstance(timing, dict) or set(timing) != TIMING
            or timing['schema_version'] != 'aster-answer-holdout-direct-timing.v1'
            or timing['timing_scope'] != 'direct backend; not Aster/Companion user latency'
            or not isinstance(timing['status_counts'], dict)):
        raise ValueError('unsupported timing boundary')
    digest(timing['attempts_sha256'])
    for n in timing['status_counts'].values(): count(n)
    if timing['status_counts'] != dict(statuses):
        raise ValueError('timing attempt counts disagree')
    for key in ('completed_median_ms', 'completed_max_ms'):
        n = timing[key]
        if statuses['completed'] == 0:
            if n is not None: raise ValueError('completion timing without completion')
        elif type(n) not in (int, float) or not math.isfinite(n) or not 0 <= n <= 600000:
            raise ValueError('invalid completion timing')
    if statuses['completed'] and timing['completed_median_ms'] > timing['completed_max_ms']:
        raise ValueError('median exceeds maximum')
    return value


def compare(first_raw, first_sha, second_raw, second_sha):
    first = load(first_raw, first_sha); second = load(second_raw, second_sha)
    if (first['packet_sha256'] != second['packet_sha256']
            or first['direct_backend_timing'] != second['direct_backend_timing']):
        raise ValueError('reviews do not bind the same captured run')
    a = {row['case_id']: row for row in first['cases']}
    b = {row['case_id']: row for row in second['cases']}
    if a.keys() != b.keys(): raise ValueError('review case sets differ')
    fixed = ('class', 'expected_outcome', 'attempt_status')
    if any(any(a[key][field] != b[key][field] for field in fixed) for key in a):
        raise ValueError('review input identities disagree')
    return {'schema': 'b60-adaptive-holdout-receipt.v1',
            'publication_digests': [first_sha, second_sha],
            'cases': len(a), 'case_pass_agreement': sum(a[k]['passed'] == b[k]['passed'] for k in a),
            'outcome_agreement': sum(a[k]['reviewer_outcome'] == b[k]['reviewer_outcome'] for k in a),
            'reported_counts': [first['counts'], second['counts']],
            'reported_classes': [first['classes'], second['classes']],
            'reported_direct_timing': first['direct_backend_timing'],
            'useful_answer_p50_seconds': None, 'useful_answer_p95_seconds': None,
            'qualification_eligible': False, 'deployment_authorized': False,
            'limits': ['Published supplied labels, not independent ground truth',
                       'Raw capture and reviewer packets not reproduced here',
                       'No full Aster path or per-class latency budget',
                       'Agreement does not prove review independence or safe tool use']}
