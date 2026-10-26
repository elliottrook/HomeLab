"""Home timestamp gate only, not a household-value validator or device adapter."""
from dataclasses import dataclass
from datetime import datetime

MAX_AGE_SECONDS = 600
FUTURE_SKEW_SECONDS = 300


@dataclass(frozen=True)
class Freshness:
    state: str
    publication_age: float = None
    source_age: float = None

    @property
    def permits_value_validation(self):
        return self.state == 'fresh'


def _stamp(value):
    if not isinstance(value,str) or not 10 <= len(value) <= 80:
        raise ValueError('home-timestamp-format')
    result = datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.utcoffset() is None: raise ValueError('home-timestamp-zone')
    return result


def assess(payload, now):
    """A newly copied old source cannot become live household state.

    The caller must separately bound/read/validate the value contract before
    exposing any values. This function has no I/O and retains none of them.
    """
    if not isinstance(now,datetime) or now.utcoffset() is None:
        raise ValueError('home-aware-clock-required')
    if payload is None: return Freshness('missing')
    try:
        if (not isinstance(payload,dict) or type(payload.get('schema_version')) is not int
                or payload['schema_version'] != 1):
            return Freshness('invalid')
        snapshot = payload.get('snapshot')
        if (not isinstance(snapshot,dict) or type(snapshot.get('schema_version')) is not int
                or snapshot['schema_version'] != 3):
            return Freshness('invalid')
        publication = _stamp(payload.get('generated_at'))
        source = _stamp(payload.get('source_updated_at'))
        publication_age = (now-publication).total_seconds()
        source_age = (now-source).total_seconds()
        if min(publication_age,source_age) < -FUTURE_SKEW_SECONDS:
            return Freshness('future',publication_age,source_age)
        if (source-publication).total_seconds() > FUTURE_SKEW_SECONDS:
            return Freshness('invalid',publication_age,source_age)
        if max(publication_age,source_age) > MAX_AGE_SECONDS:
            return Freshness('stale',publication_age,source_age)
        return Freshness('fresh',publication_age,source_age)
    except (ValueError,TypeError,OverflowError):
        return Freshness('invalid')
