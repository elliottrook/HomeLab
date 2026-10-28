"""Pure content-free phase timing proposal, not an admitted runner adapter.

The owning runner must capture monotonic timestamps and preserve custody.
Caller-supplied timestamps/digests do not authenticate observations. No clock,
transport, process, filesystem writer or deployment path exists here.
"""
import copy
import re

PHASES = ('drain', 'candidate_setup', 'workload', 'accepted_restore',
          'final_verification')
RECOVERY = {'accepted_restore', 'final_verification'}
BINDINGS = {'run_id', 'lease_id', 'generation', 'model_sha256', 'runtime_sha256',
            'checkpoint_sha256', 'source_sha256'}


def summarize(bindings, phases):
    if not isinstance(bindings, dict) or set(bindings) != BINDINGS:
        raise ValueError('exact proposal bindings required')
    for name in ('run_id', 'lease_id'):
        value = bindings[name]
        if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_.:-]{0,95}', value):
            raise ValueError('bounded opaque identity required')
    if type(bindings['generation']) is not int or bindings['generation'] < 1:
        raise ValueError('positive lease generation required')
    for name in BINDINGS - {'run_id', 'lease_id', 'generation'}:
        if (not isinstance(bindings[name], str)
                or not re.fullmatch(r'[0-9a-f]{64}', bindings[name])):
            raise ValueError('exact digest required')
    if not isinstance(phases, list) or len(phases) != len(PHASES):
        raise ValueError('all phase outcomes required, including unattempted phases')
    rows, first, last, failed = [], None, None, False
    open_interval_seen = False
    for expected, row in zip(PHASES, phases):
        if (not isinstance(row, dict)
                or set(row) != {'phase', 'started_ns', 'finished_ns', 'outcome'}
                or row['phase'] != expected or not isinstance(row['outcome'], str)
                or row['outcome'] not in {'completed', 'failed', 'uncertain', 'not_attempted'}):
            raise ValueError('phase order or closed schema differs')
        start, end, outcome = row['started_ns'], row['finished_ns'], row['outcome']
        if outcome == 'not_attempted':
            if start is not None or end is not None:
                raise ValueError('unattempted phase cannot claim timing')
            failed = True
            elapsed = None
        elif outcome == 'uncertain' and end is None:
            if (type(start) is not int or not 0 <= start <= 2**63 - 1
                    or (last is not None and start < last)
                    or (failed and expected not in RECOVERY)):
                raise ValueError('invalid interrupted phase boundary')
            first = start if first is None else first
            last, failed, open_interval_seen = start, True, True
            elapsed = None
        else:
            if (type(start) is not int or type(end) is not int
                    or not 0 <= start <= end <= 2**63 - 1
                    or (last is not None and start < last)):
                raise ValueError('ordered bounded monotonic interval required')
            if failed and expected not in RECOVERY:
                raise ValueError('candidate work cannot continue after failure or skip')
            first = start if first is None else first
            last = end
            elapsed = end - start
            failed = failed or outcome != 'completed'
        rows.append({**row, 'elapsed_ns': elapsed})
    return {'schema': 'b60-phase-timing-proposal.v0',
            'bindings': copy.deepcopy(bindings), 'phases': rows,
            'observed_span_ns': None if first is None or open_interval_seen else last - first,
            'all_phases_completed': not failed,
            'timing_origin': 'caller_supplied_monotonic_not_authenticated',
            'qualification_eligible': False, 'live_admission_authorized': False}
