"""Label-free package validation and durable offline-injectable evaluation loop.

No network or credentials here. A separately approved transport is injected.
Never read answer keys. Do not automatically replay an uncertain session.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
from sa3_investigation import investigate
from validate_sa3_holdout_release import validate_release


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


def run_package(bundle, manifest, ledger, transport, ready, model='qwen3.8-27b', engine=investigate):
    """Run/resume only when separately approved; ready() must verify idle/healthy.

    Hash-chained private journal is locked for the run. Incomplete writes or an
    unmatched start block resume. Completed sessions are never silently replayed.
    """
    cases = validate_cases(bundle, manifest)
    plan = schedule(cases)
    allowed = {(c['id'], mode) for c, mode in plan}
    ledger = Path(ledger)
    fd = os.open(ledger, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+', encoding='utf-8') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stat = os.fstat(stream.fileno())
        if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            raise ValueError('ledger must be owner-only')
        raw = stream.read()
        if raw and not raw.endswith('\n'):
            raise ValueError('partial journal; manual reconciliation required')
        previous, active, done = '', None, set()
        for line in raw.splitlines():
            row = json.loads(line)
            sealed = dict(row); stored = sealed.pop('digest')
            if row['previous'] != previous or digest(sealed) != stored or row['release'] != manifest['release_digest']:
                raise ValueError('journal integrity/release mismatch')
            previous = stored
            event = row['event']
            if event['type'] == 'started':
                pair = (event['case_id'], event['mode'])
                if active is not None or pair in done or pair not in allowed:
                    raise ValueError('invalid session sequence')
                active = pair
            elif event['type'] == 'finished':
                pair = (event['result']['case_id'], event['result']['mode'])
                if pair != active:
                    raise ValueError('completion without matching start')
                status = event['result']['status']
                if status.startswith('transport_error') or status == 'time_budget_exhausted':
                    raise ValueError('failed session requires explicit reconciliation; no replay')
                done.add(pair); active = None
            elif event['type'] != 'paused':
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
            result = engine(case, mode, model, transport)
            append({'type': 'finished', 'result': result})
            if result['status'].startswith('transport_error') or result['status'] == 'time_budget_exhausted':
                return {'status': 'stopped', 'completed_sessions': len(done), 'reconciliation_required': True}
            done.add((case['id'], mode))
        return {'status': 'complete', 'completed_sessions': len(done), 'ledger_digest': previous}
