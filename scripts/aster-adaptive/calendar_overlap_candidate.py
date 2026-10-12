"""Offline H-A1 candidate: occupancy from authorized normalized intervals.

No calendar access, natural-language parsing, recurrence expansion or routing.
An upstream trusted adapter must normalize events and assert completeness.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _instant(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp needs an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def occupancy(request: dict) -> dict:
    """Return busy/free/unknown; only exact, fresh, complete inputs yield free."""
    if not isinstance(request, dict) or set(request) != {
        "calendar_id", "access_granted", "complete", "observed_at",
        "now", "max_age_seconds", "start", "end", "events",
    }:
        raise ValueError("invalid request fields")
    calendar_id = request["calendar_id"]
    if not isinstance(calendar_id, str) or not calendar_id or len(calendar_id) > 128:
        raise ValueError("invalid calendar identity")
    if type(request["access_granted"]) is not bool or type(request["complete"]) is not bool:
        raise ValueError("invalid access/completeness flags")
    if not request["access_granted"]:
        return {"status": "unknown", "reason": "calendar_access_denied"}
    if not request["complete"]:
        return {"status": "unknown", "reason": "incomplete_calendar_window"}
    age_limit = request["max_age_seconds"]
    if type(age_limit) is not int or not 0 <= age_limit <= 86_400:
        raise ValueError("invalid freshness limit")
    observed, now = _instant(request["observed_at"]), _instant(request["now"])
    if observed > now or now - observed > timedelta(seconds=age_limit):
        return {"status": "unknown", "reason": "stale_or_future_observation"}
    start, end = _instant(request["start"]), _instant(request["end"])
    if end <= start or end - start > timedelta(days=1):
        raise ValueError("invalid requested interval")
    events = request["events"]
    if not isinstance(events, list) or len(events) > 500:
        raise ValueError("invalid event set")
    intervals = []
    for event in events:
        if not isinstance(event, dict) or set(event) != {
            "calendar_id", "start", "end", "recurrence_expanded",
        }:
            raise ValueError("invalid event fields")
        if event["calendar_id"] != calendar_id or type(event["recurrence_expanded"]) is not bool:
            return {"status": "unknown", "reason": "untrusted_event_scope"}
        if not event["recurrence_expanded"]:
            return {"status": "unknown", "reason": "unexpanded_recurrence"}
        event_start, event_end = _instant(event["start"]), _instant(event["end"])
        if event_end <= event_start:
            raise ValueError("invalid event interval")
        intervals.append((event_start, event_end))
    if any(start < event_end and event_start < end
           for event_start, event_end in intervals):
        return {"status": "busy", "reason": "overlap"}
    return {"status": "free", "reason": "complete_window_no_overlap"}
