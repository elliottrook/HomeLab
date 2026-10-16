"""Offline timing proposal; supplied budgets are assumptions, not measured proof.

Does not authenticate a receipt, invoke a timer, admit a batch or modify the
Adaptive owner's guard. Platform must establish the recovery/trigger-lag bounds.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo('America/Vancouver')
MIN_RECOVERY_SECONDS = 900


def review(trigger_at, *, recovery_seconds, trigger_lag_seconds):
    if (not isinstance(trigger_at, datetime) or trigger_at.tzinfo is None
            or trigger_at.utcoffset() is None):
        raise ValueError('aware recovery trigger required')
    if (type(recovery_seconds) is not int or recovery_seconds < MIN_RECOVERY_SECONDS
            or type(trigger_lag_seconds) is not int or trigger_lag_seconds < 1
            or recovery_seconds + trigger_lag_seconds >= 86400):
        raise ValueError('bounded recovery and trigger-lag budgets required')
    trigger = trigger_at.astimezone(TZ)
    cutoff = trigger.replace(hour=4, minute=15, second=0, microsecond=0)
    budget = timedelta(seconds=recovery_seconds + trigger_lag_seconds)
    completion = (trigger.astimezone(timezone.utc) + budget).astimezone(TZ)
    latest_trigger = (cutoff.astimezone(timezone.utc) - budget).astimezone(TZ)
    if completion.astimezone(timezone.utc) >= cutoff.astimezone(timezone.utc):
        raise ValueError('recovery cannot complete before 04:15')
    return {'schema': 'b60-recovery-margin-proposal.v0',
            'assumed_latest_completion_at': completion.isoformat(),
            'trigger_must_be_before': latest_trigger.isoformat(),
            'budgets_measured': False, 'live_admission_authorized': False}
