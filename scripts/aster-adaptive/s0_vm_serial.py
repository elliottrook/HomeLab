"""Strict, bounded S0 VM serial framing. Pure functions; no I/O or CLI."""

import base64
import binascii
import hashlib
import json
import math
import re


PREFIX = b'ASTER_S0_V1'
MAX_CAPTURE = 4 * 1024 * 1024
MAX_RESULT = 2 * 1024 * 1024
CHUNK_BYTES = 3072
MAX_LINE = 4608
ID = re.compile(rb'[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z')
SHA256 = re.compile(rb'[0-9a-f]{64}\Z')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON key')
        value[key] = item
    return value


def _nonfinite(_):
    raise ValueError('nonfinite JSON')


def _integer(raw, name):
    if not raw or (raw != b'0' and raw.startswith(b'0')) or not raw.isdigit():
        raise ValueError('invalid ' + name)
    return int(raw)


def _identity(run_id, manifest_sha256):
    if isinstance(run_id, str):
        run_id = run_id.encode('ascii')
    if isinstance(manifest_sha256, str):
        manifest_sha256 = manifest_sha256.encode('ascii')
    if not ID.fullmatch(run_id or b''):
        raise ValueError('invalid run id')
    if not SHA256.fullmatch(manifest_sha256 or b''):
        raise ValueError('invalid manifest digest')
    return run_id, manifest_sha256


def encode_result(result, run_id, manifest_sha256):
    """Encode canonical JSON for fixture/protocol tests; returns serial lines."""
    run_id, manifest_sha256 = _identity(run_id, manifest_sha256)
    raw = _canonical(result)
    if not raw or len(raw) > MAX_RESULT:
        raise ValueError('result size')
    digest = hashlib.sha256(raw).hexdigest().encode('ascii')
    parts = [raw[i:i + CHUNK_BYTES] for i in range(0, len(raw), CHUNK_BYTES)]
    lines = [b' '.join((PREFIX, b'BEGIN', run_id, manifest_sha256,
                        str(len(raw)).encode(), digest, str(len(parts)).encode()))]
    for sequence, part in enumerate(parts):
        lines.append(b' '.join((PREFIX, b'CHUNK', run_id,
                                str(sequence).encode(), base64.b64encode(part))))
    lines.append(b' '.join((PREFIX, b'END', run_id, str(len(raw)).encode(), digest)))
    if any(len(line) > MAX_LINE for line in lines):
        raise ValueError('protocol line size')
    return b'\n'.join(lines) + b'\n'


def decode_capture(capture, expected_run_id, expected_manifest_sha256):
    """Extract exactly one complete result from a bounded mixed serial capture."""
    if type(capture) is not bytes or len(capture) > MAX_CAPTURE:
        raise ValueError('capture size')
    run_id, manifest = _identity(expected_run_id, expected_manifest_sha256)
    begun = ended = False
    declared_bytes = declared_chunks = None
    declared_digest = None
    chunks = []
    for original in capture.splitlines():
        line = original[:-1] if original.endswith(b'\r') else original
        if not line.startswith(PREFIX):
            continue
        if len(line) > MAX_LINE:
            raise ValueError('protocol line size')
        fields = line.split(b' ')
        if len(fields) < 2 or fields[0] != PREFIX:
            raise ValueError('malformed protocol record')
        kind = fields[1]
        if ended:
            raise ValueError('protocol record after end')
        if kind == b'BEGIN':
            if begun or len(fields) != 7:
                raise ValueError('invalid begin')
            if fields[2] != run_id or fields[3] != manifest:
                raise ValueError('unexpected identity')
            declared_bytes = _integer(fields[4], 'byte count')
            declared_chunks = _integer(fields[6], 'chunk count')
            if not 0 < declared_bytes <= MAX_RESULT or not 0 < declared_chunks <= math.ceil(MAX_RESULT / CHUNK_BYTES):
                raise ValueError('declared bounds')
            if declared_chunks != math.ceil(declared_bytes / CHUNK_BYTES) or not SHA256.fullmatch(fields[5]):
                raise ValueError('inconsistent begin')
            declared_digest = fields[5]
            begun = True
        elif kind == b'CHUNK':
            if not begun or len(fields) != 5 or fields[2] != run_id:
                raise ValueError('invalid chunk')
            sequence = _integer(fields[3], 'sequence')
            if sequence != len(chunks) or sequence >= declared_chunks:
                raise ValueError('chunk sequence')
            try:
                part = base64.b64decode(fields[4], validate=True)
            except (binascii.Error, ValueError):
                raise ValueError('invalid chunk encoding') from None
            expected = CHUNK_BYTES if sequence < declared_chunks - 1 else declared_bytes - CHUNK_BYTES * sequence
            if len(part) != expected:
                raise ValueError('chunk size')
            chunks.append(part)
        elif kind == b'END':
            if not begun or len(fields) != 5 or fields[2] != run_id:
                raise ValueError('invalid end')
            if _integer(fields[3], 'end byte count') != declared_bytes or fields[4] != declared_digest:
                raise ValueError('inconsistent end')
            if len(chunks) != declared_chunks:
                raise ValueError('incomplete chunks')
            ended = True
        else:
            raise ValueError('unknown protocol record')
    if not begun or not ended:
        raise ValueError('incomplete protocol')
    raw = b''.join(chunks)
    if len(raw) != declared_bytes or hashlib.sha256(raw).hexdigest().encode() != declared_digest:
        raise ValueError('result digest')
    try:
        value = json.loads(raw, object_pairs_hook=_unique, parse_constant=_nonfinite)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError('invalid result JSON') from None
    if _canonical(value) != raw:
        raise ValueError('noncanonical result JSON')
    return {'run_id': run_id.decode(), 'manifest_sha256': manifest.decode(),
            'bytes': len(raw), 'sha256': declared_digest.decode(),
            'result_bytes': raw, 'result': value}

