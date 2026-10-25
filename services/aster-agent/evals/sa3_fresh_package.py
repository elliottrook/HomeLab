"""Label-free package validation and durable offline-injectable evaluation loop.

No network or credentials here. A separately approved transport is injected.
Never read answer keys. Do not automatically replay an uncertain session.
"""
import copy
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
from sa3_investigation import investigate
from validate_sa3_holdout_release import validate_release


MAX_LEDGER_BYTES = 4 * 1024 * 1024
ENGINE_STATUSES = frozenset({
    'call_budget_exhausted',
    'time_budget_exhausted',
    'invalid_transport_response',
    'invalid_transport_metadata',
    'incomplete_or_tool_output',
    'invalid_answer',
    'effect_claim_rejected',
    'unobserved_evidence_rejected',
    'check_rejected',
    'invalid_terminal_check',
    'conclude',
    'clarify',
})
TRANSPORT_ERROR = re.compile(r'^transport_error:[A-Za-z_][A-Za-z0-9_]{0,127}$')


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON key in private journal')
        value[key] = item
    return value


def _reject_non_json_constant(value):
    raise ValueError(f'non-JSON numeric constant in private journal: {value}')


def decode_journal_json(raw):
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_constant=_reject_non_json_constant)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_cases(bundle, manifest):
    if validate_release(manifest) or manifest.get('status') != 'sealed':
        raise ValueError('valid sealed release required')
    if not isinstance(bundle, dict) or set(bundle) != {'schema_version', 'cases'} or bundle['schema_version'] != 1:
        raise ValueError('invalid case bundle')
    cases = bundle['cases']
    if not isinstance(cases, list) or len(cases) != 20:
        raise ValueError('exactly twenty cases required')
    expected = {c['id']: c['case_hash'] for c in manifest['cases']}
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {'id', 'prompt', 'capabilities', 'initial_observations', 'responses'}:
            raise ValueError('case fields invalid; labels prohibited')
        ident = case['id']
        if not isinstance(ident, str) or ident in seen or ident not in expected or digest(case) != expected[ident]:
            raise ValueError('case identity/digest mismatch')
        seen.add(ident)
        if not isinstance(case['prompt'], str) or not case['prompt'].strip():
            raise ValueError('invalid prompt')
        if len(json.dumps(case).encode()) > 16000:
            raise ValueError('case exceeds development envelope')
        caps = case['capabilities']
        if not isinstance(caps, list) or not 2 <= len(caps) <= 3:
            raise ValueError('invalid catalogue')
        for cap in caps:
            if (not isinstance(cap, dict) or set(cap) != {'id', 'description'}
                    or any(not isinstance(v, str) or not v.strip() for v in cap.values())):
                raise ValueError('invalid capability')
        ids = [c['id'] for c in caps]
        if len(ids) != len(set(ids)) or not isinstance(case['responses'], dict) or set(ids) != set(case['responses']):
            raise ValueError('catalogue/response mismatch')
        initial = case['initial_observations']
        if not isinstance(initial, list) or not initial:
            raise ValueError('initial observations required')
        observations = initial + list(case['responses'].values())
        evidence_ids = []
        for obs in observations:
            if (not isinstance(obs, dict) or set(obs) != {'id', 'freshness', 'text'}
                    or any(not isinstance(v, str) or not v.strip() for v in obs.values())
                    or obs['freshness'] not in ('current', 'stale', 'unavailable')):
                raise ValueError('invalid observation')
            evidence_ids.append(obs['id'])
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError('duplicate observation ID')
    return copy.deepcopy(cases)


def schedule(cases):
    result = []
    for i, case in enumerate(sorted(cases, key=lambda x: x['id'])):
        modes = ['nonthinking', 'thinking_compact']
        if i % 2:
            modes.reverse()
        result.extend((case, mode) for mode in modes)
    return result


def validate_engine_result(result, case_id, mode):
    """Reject unbounded or raw engine output before it reaches the journal."""
    allowed = {'case_id', 'mode', 'status', 'steps', 'checks', 'observations',
               'elapsed_seconds', 'attempted_calls', 'failure', 'limit'}
    required = {'case_id', 'mode', 'status', 'steps'}
    if (not isinstance(result, dict) or not required <= set(result)
            or not set(result) <= allowed or result.get('case_id') != case_id
            or result.get('mode') != mode or not isinstance(result.get('status'), str)
            or (result['status'] not in ENGINE_STATUSES
                and TRANSPORT_ERROR.fullmatch(result['status']) is None)
            or not isinstance(result.get('steps'), list)):
        raise ValueError('invalid engine result; manual reconciliation required')
    try:
        encoded = json.dumps(
            result, sort_keys=True, separators=(',', ':'), allow_nan=False
        ).encode()
    except (TypeError, ValueError) as exc:
        raise ValueError(
            'engine result is not finite JSON; manual reconciliation required'
        ) from exc
    if len(encoded) > 65_536:
        raise ValueError('engine result exceeds journal envelope; manual reconciliation required')
    if len(result['steps']) > 3:
        raise ValueError('invalid engine result; manual reconciliation required')
    for step in result['steps']:
        if (not isinstance(step, dict) or set(step) != {'metadata', 'answer'}
                or not isinstance(step['metadata'], dict)
                or not set(step['metadata']) <= {
                    'latency_seconds', 'finish_reason', 'reasoning_present',
                    'reasoning_characters', 'completion_tokens'}):
            raise ValueError('invalid engine result; manual reconciliation required')
        metadata = step['metadata']
        if ('latency_seconds' in metadata
                and (type(metadata['latency_seconds']) not in (int, float)
                     or not math.isfinite(metadata['latency_seconds'])
                     or metadata['latency_seconds'] < 0)):
            raise ValueError('invalid engine result; manual reconciliation required')
        if ('finish_reason' in metadata
                and (not isinstance(metadata['finish_reason'], str)
                     or not 0 < len(metadata['finish_reason']) <= 64)):
            raise ValueError('invalid engine result; manual reconciliation required')
        if ('reasoning_present' in metadata
                and type(metadata['reasoning_present']) is not bool):
            raise ValueError('invalid engine result; manual reconciliation required')
        for field in ('reasoning_characters', 'completion_tokens'):
            if field in metadata and (type(metadata[field]) is not int or metadata[field] < 0):
                raise ValueError('invalid engine result; manual reconciliation required')
        answer = step['answer']
        if answer is not None:
            if (not isinstance(answer, dict) or set(answer) != {
                    'decision', 'check', 'evidence_ids', 'summary', 'effects'}
                    or answer['decision'] not in ('check', 'conclude', 'clarify')
                    or not isinstance(answer['check'], str)
                    or not isinstance(answer['evidence_ids'], list)
                    or any(not isinstance(item, str) for item in answer['evidence_ids'])
                    or len(answer['evidence_ids']) != len(set(answer['evidence_ids']))
                    or not isinstance(answer['summary'], str)
                    or not 0 < len(answer['summary']) <= 4000
                    or answer['effects'] != []):
                raise ValueError('invalid engine result; manual reconciliation required')
    if 'checks' in result and (not isinstance(result['checks'], list)
            or len(result['checks']) > 2
            or any(not isinstance(item, str) for item in result['checks'])
            or len(result['checks']) != len(set(result['checks']))):
        raise ValueError('invalid engine result; manual reconciliation required')
    if 'observations' in result and (not isinstance(result['observations'], list)
            or any(not isinstance(item, dict)
                   or set(item) != {'id', 'freshness', 'text'}
                   or any(not isinstance(item[field], str) or not item[field].strip()
                          for field in ('id', 'freshness', 'text'))
                   or item['freshness'] not in ('current', 'stale', 'unavailable')
                   for item in result['observations'])):
        raise ValueError('invalid engine result; manual reconciliation required')
    if 'elapsed_seconds' in result and (
            type(result['elapsed_seconds']) not in (int, float)
            or not math.isfinite(result['elapsed_seconds'])
            or result['elapsed_seconds'] < 0):
        raise ValueError('invalid engine result; manual reconciliation required')
    if 'attempted_calls' in result and (
            type(result['attempted_calls']) is not int
            or not 0 <= result['attempted_calls'] <= 3):
        raise ValueError('invalid engine result; manual reconciliation required')
    if 'failure' in result and result['failure'] is not None:
        failure = result['failure']
        if (not isinstance(failure, dict) or set(failure) != {
                'type', 'attempt', 'elapsed_seconds', 'request_timeout_seconds'}
                or not isinstance(failure['type'], str)
                or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}', failure['type'])
                or type(failure['attempt']) is not int or not 1 <= failure['attempt'] <= 3
                or type(failure['elapsed_seconds']) not in (int, float)
                or not math.isfinite(failure['elapsed_seconds'])
                or failure['elapsed_seconds'] < 0
                or type(failure['request_timeout_seconds']) not in (int, float)
                or not math.isfinite(failure['request_timeout_seconds'])
                or not 0 < failure['request_timeout_seconds'] <= 240):
            raise ValueError('invalid engine result; manual reconciliation required')
    if ('limit' in result and result['limit'] !=
            'synthetic development only; terminal status is not a correctness grade'):
        raise ValueError('invalid engine result; manual reconciliation required')
    if result['status'] in ('conclude', 'clarify'):
        if (not result['steps'] or result['steps'][-1]['answer'] is None
                or result['steps'][-1]['answer']['decision'] != result['status']
                or result['steps'][-1]['answer']['check'] != ''):
            raise ValueError('terminal status and final answer disagree; manual reconciliation required')
    elif any(step['answer'] is not None
             and step['answer']['decision'] in ('conclude', 'clarify')
             for step in result['steps']):
        raise ValueError('nonterminal status carries terminal answer; manual reconciliation required')
    transport_failure = result['status'].startswith('transport_error')
    has_failure = result.get('failure') is not None
    if transport_failure != has_failure:
        raise ValueError('transport status and failure metadata disagree; manual reconciliation required')
    if 'attempted_calls' in result:
        expected_attempts = len(result['steps']) + int(transport_failure)
        if result['attempted_calls'] != expected_attempts:
            raise ValueError('attempt count and retained steps disagree; manual reconciliation required')
    return copy.deepcopy(result)


def run_package(
        bundle, manifest, ledger, transport, ready, model='qwen3.8-27b',
        engine=investigate, case_validator=validate_cases, planner=schedule):
    """Run/resume only when separately approved; ready() must verify idle/healthy.

    Hash-chained private journal is locked for the run. Incomplete writes or an
    unmatched start block resume. Completed sessions are never silently replayed.
    """
    cases = case_validator(bundle, manifest)
    plan = planner(cases)
    allowed = {(c['id'], mode) for c, mode in plan}
    ledger = Path(ledger)
    fd = os.open(ledger, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+', encoding='utf-8') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stat = os.fstat(stream.fileno())
        if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            raise ValueError('ledger must be owner-only')
        if stat.st_size > MAX_LEDGER_BYTES:
            raise ValueError('ledger exceeds the bounded evidence envelope')
        raw = stream.read()
        if raw and not raw.endswith('\n'):
            raise ValueError('partial journal; manual reconciliation required')
        previous, active, done = '', None, set()
        for line in raw.splitlines():
            row = decode_journal_json(line)
            if not isinstance(row, dict) or set(row) != {'release', 'previous', 'event', 'digest'}:
                raise ValueError('invalid journal row shape')
            sealed = dict(row); stored = sealed.pop('digest')
            if row['previous'] != previous or digest(sealed) != stored or row['release'] != manifest['release_digest']:
                raise ValueError('journal integrity/release mismatch')
            previous = stored
            event = row['event']
            if not isinstance(event, dict) or not isinstance(event.get('type'), str):
                raise ValueError('invalid journal event')
            if event['type'] == 'started':
                if set(event) != {'type', 'case_id', 'mode'}:
                    raise ValueError('invalid started event')
                pair = (event['case_id'], event['mode'])
                if active is not None or pair in done or pair not in allowed:
                    raise ValueError('invalid session sequence')
                active = pair
            elif event['type'] == 'finished':
                if set(event) != {'type', 'result'} or not isinstance(event['result'], dict):
                    raise ValueError('invalid finished event')
                raw_result = event['result']
                result = validate_engine_result(
                    raw_result, raw_result.get('case_id'), raw_result.get('mode')
                )
                pair = (result['case_id'], result['mode'])
                if pair != active:
                    raise ValueError('completion without matching start')
                status = result['status']
                if status.startswith('transport_error') or status == 'time_budget_exhausted':
                    raise ValueError('failed session requires explicit reconciliation; no replay')
                done.add(pair); active = None
            elif event['type'] == 'paused':
                if set(event) != {'type', 'reason'} or event['reason'] != 'not_confirmed_idle_healthy':
                    raise ValueError('invalid paused event')
            else:
                raise ValueError('unknown journal event')
        if active is not None:
            raise ValueError('uncertain session; no replay')

        def append(event):
            nonlocal previous
            row = {'release': manifest['release_digest'], 'previous': previous, 'event': event}
            row['digest'] = digest(row)
            stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
            previous = row['digest']

        for case, mode in plan:
            if (case['id'], mode) in done:
                continue
            if not ready():
                append({'type': 'paused', 'reason': 'not_confirmed_idle_healthy'})
                return {'status': 'paused', 'completed_sessions': len(done)}
            append({'type': 'started', 'case_id': case['id'], 'mode': mode})
            result = validate_engine_result(engine(case, mode, model, transport),
                                            case['id'], mode)
            append({'type': 'finished', 'result': result})
            if result['status'].startswith('transport_error') or result['status'] == 'time_budget_exhausted':
                return {'status': 'stopped', 'completed_sessions': len(done), 'reconciliation_required': True}
            done.add((case['id'], mode))
        return {'status': 'complete', 'completed_sessions': len(done), 'ledger_digest': previous}
