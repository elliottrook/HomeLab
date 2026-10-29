"""Offline projection of sanitized exclusive-session metadata; never admission.

Callers must independently establish custody, source pins, current lock state,
and live health. Matching JSON is not authenticated restoration evidence.
No filesystem, network, subprocess, model or deployment operations occur here.
"""
import hashlib
import json


def project(session, entry, reservation, *, booking_id, owner):
    """Cross-check the installed v1 core/ledger fields without granting authority."""
    result = {'advisory_only': True, 'model_success': False,
              'live_qualification_proven': False, 'status': 'inconsistent'}
    if not all(isinstance(row, dict) for row in (session, entry, reservation)):
        return result
    if (session.get('schema') != 'aster-exclusive-session.v1'
            or entry.get('schema') != 'aster-entry-snapshot.v1'
            or any(row.get('booking_id') != booking_id or row.get('owner') != owner
                   for row in (session, reservation))):
        return result
    try:
        digest = hashlib.sha256(json.dumps(
            entry, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    except (TypeError, ValueError, RecursionError):
        return result
    if session.get('entry_sha256') != digest:
        return result
    phase = session.get('phase')
    if phase not in {'released', 'released-late'}:
        result['status'] = 'not-terminal'
        return result
    if (session.get('production_restored') is not True
            or type(session.get('deadline_missed')) is not bool
            or type(session.get('trial_failed')) is not bool
            or type(session.get('updated_epoch')) is not int
            or type(session.get('restore_deadline')) is not int
            or session['deadline_missed'] != (phase == 'released-late')
            or session['deadline_missed'] != (
                session['updated_epoch'] >= session['restore_deadline'])
            or reservation.get('entry_sha256') != digest):
        return result
    failed = session['trial_failed'] or session['deadline_missed']
    if (reservation.get('state') != ('failed' if failed else 'complete')
            or reservation.get('result_code') != (
                'FAILED_RESTORED' if failed else 'RESTORED')):
        return result
    result['status'] = ('late-restoration-reported' if session['deadline_missed'] else
                        'failed-trial-restoration-reported' if session['trial_failed'] else
                        'restoration-reported-awaiting-independent-verification')
    return result
