"""Offline partial-release algorithm for platform-owner review, not a live lease.

No SSH, services, files, locks, admission or scheduler. Callbacks are fake in
tests. The platform owner must supply durable state, exact health/device gates
and independent recovery before adopting this into its controller.
"""
import copy

SERVICES = {'104:aster-agent.service', '110:aster-llama.service',
            '116:aster-speech.service'}


class RecoveryReviewRequired(RuntimeError):
    pass


def restore_record(record, *, active, start, persist, validate):
    state = copy.deepcopy(record)
    if state.get('state') not in {'leased', 'restoring', 'restoration_validated'}:
        raise ValueError('not a restorable lease record')
    services = state.get('services')
    attempted = state.get('restore_attempted', [])
    if (not isinstance(services, list) or not isinstance(attempted, list)
            or any(not isinstance(k, str) or k not in SERVICES for k in services)
            or len(services) != len(set(services))
            or any(k not in services for k in attempted)
            or len(attempted) != len(set(attempted))):
        raise ValueError('unexpected restoration targets')
    state['state'] = 'restoring'
    state['restore_attempted'] = attempted
    persist(copy.deepcopy(state))
    for key in services:
        observed = active(key)
        if type(observed) is not bool:
            raise RecoveryReviewRequired('service state unknown; keep lease locked')
        if observed:
            continue
        if key in attempted:
            raise RecoveryReviewRequired('prior start unconfirmed; no automatic restart retry')
        # Seal intent before effects: an interrupted/uncertain start is not
        # permission to retry a GPU/service start on the next invocation.
        attempted.append(key)
        persist(copy.deepcopy(state))
        start(key)
        if active(key) is not True:
            raise RecoveryReviewRequired('service start unconfirmed; keep lease locked')
    # Unit-active alone does not certify accepted SYCL/device/auth correctness.
    if validate() is not True:
        raise RecoveryReviewRequired('exact restoration validation failed; keep lease locked')
    state['state'] = 'restoration_validated'
    persist(copy.deepcopy(state))
    return state
