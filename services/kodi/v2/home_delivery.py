"""Pure HA-export capture validation. No network, files, publication or retries."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re

from home_dashboard_model import project

MAX_SOURCE_BYTES = 262144
MAX_CAPTURE_BYTES = 524288
SOURCE_KEYS = {'schema_version', 'snapshot_id', 'lights', 'temperatures',
               'weather', 'rooms', 'entities', 'timers', 'media_providers'}


def require(value, code):
    if not value:
        raise ValueError(code)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'home-capture-duplicate-field')
        result[key] = value
    return result


def reject_constant(_value):
    raise ValueError('home-capture-nonfinite')


@dataclass(frozen=True)
class Prepared:
    """Sensitive bytes deliberately excluded from repr; never a log record."""
    source_updated_at: str
    counts: tuple
    encoded: bytes = field(repr=False)


def prepare(raw, now):
    """Accept one stable regular mode0600 source generation, or fail closed.

    The source-local reader must have projected/validated before transport.
    A successful return is a candidate only, not permission to publish it.
    """
    require(isinstance(now, datetime) and now.utcoffset() is not None,
            'home-capture-aware-clock')
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_CAPTURE_BYTES,
            'home-capture-size')
    try:
        capture = json.loads(raw, object_pairs_hook=unique_object,
                             parse_constant=reject_constant)
        require(isinstance(capture, dict) and set(capture) ==
                {'capture_version', 'before', 'after', 'snapshot'}, 'home-capture-shape')
        require(type(capture['capture_version']) is int and
                capture['capture_version'] == 1, 'home-capture-version')
        before, after = capture['before'], capture['after']
        require(isinstance(before, str) and isinstance(after, str) and
                len(before) <= 400 and before == after, 'home-capture-source-changed')
        fields = before.split('|')
        require(len(fields) == 9 and all(re.fullmatch(r'[0-9]{1,20}', f)
                for f in fields[:7]), 'home-capture-metadata')
        require(0 < int(fields[2]) <= MAX_SOURCE_BYTES and fields[5:7] == ['600', '1'],
                'home-capture-source-file')
        require(all(0 < len(f) <= 80 for f in fields[7:]), 'home-capture-metadata')
        source_time = datetime.fromtimestamp(int(fields[3]), timezone.utc)
        snapshot = capture['snapshot']
        require(isinstance(snapshot, dict) and set(snapshot) == SOURCE_KEYS,
                'home-capture-source-contract')
        payload = dict(schema_version=1, generated_at=now.astimezone(timezone.utc).isoformat(),
                       source_updated_at=source_time.isoformat(), snapshot=snapshot)
        view = project(payload, now)
        require(view.state == 'fresh', 'home-capture-' + view.state)
        encoded = (json.dumps(payload, ensure_ascii=True, allow_nan=False,
                              separators=(',', ':')) + '\n').encode('ascii')
        require(len(encoded) <= MAX_SOURCE_BYTES, 'home-capture-output-size')
        return Prepared(source_time.isoformat(),
                        tuple(len(snapshot[k]) for k in ('lights', 'temperatures', 'weather')),
                        encoded)
    except (KeyError, TypeError, OverflowError, OSError, RecursionError, UnicodeError):
        raise ValueError('home-capture-invalid') from None
    except ValueError as error:
        code = str(error)
        if not re.fullmatch(r'home-capture-[a-z-]{1,60}', code):
            raise ValueError('home-capture-invalid') from None
        raise


def decode_guest_reply(raw):
    """Refuse truncation/errors before forwarding a private capture to prepare."""
    require(isinstance(raw, bytes) and 0 < len(raw) <= 1048576, 'home-capture-transport-size')
    try:
        reply = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
        require(isinstance(reply, dict) and set(reply) <=
                {'exitcode', 'exited', 'out-data', 'err-data', 'out-truncated', 'err-truncated'},
                'home-capture-guest-shape')
        require(type(reply.get('exitcode')) is int and reply['exitcode'] == 0 and
                type(reply.get('exited')) is int and reply['exited'] == 1 and
                type(reply.get('out-truncated')) is int and reply['out-truncated'] == 0 and
                type(reply.get('err-truncated', 0)) is int and
                reply.get('err-truncated', 0) == 0 and not reply.get('err-data'),
                'home-capture-guest-failed')
        value = reply.get('out-data')
        require(isinstance(value, str) and 0 < len(value) <= MAX_CAPTURE_BYTES,
                'home-capture-guest-output')
        return value.encode('utf-8')
    except (KeyError, TypeError, UnicodeError, RecursionError):
        raise ValueError('home-capture-guest-invalid') from None
    except ValueError as error:
        if not re.fullmatch(r'home-capture-[a-z-]{1,60}', str(error)):
            raise ValueError('home-capture-guest-invalid') from None
        raise
