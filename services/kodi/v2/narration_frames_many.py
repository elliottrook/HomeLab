"""Bounded AVS1 decoder for a short multi-sentence chapter proof."""
from dataclasses import dataclass
import json
import struct

MAX_HEADER = 4096
MAX_PAYLOAD = 2 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_UNITS = 32

def require(ok, code):
    if not ok:
        raise ValueError(code)

@dataclass(frozen=True)
class AudioUnit:
    index: int
    start_sample: int
    frames: int
    sample_rate: int = 24000

def read_exact(stream, size):
    raw = bytearray()
    while len(raw) < size:
        block = stream.read(size-len(raw))
        require(bool(block), 'chapter-audio-truncated-frame')
        raw.extend(block)
    return bytes(raw)

def decode(stream, request_id, expected_units):
    require(type(expected_units) is int and 2 <= expected_units <= MAX_UNITS,
            'chapter-audio-unit-count')
    units = []; pcm = bytearray(); samples = 0; ended = False
    for _ in range(expected_units + 1):
        prefix = read_exact(stream, 12)
        require(prefix[:4] == b'AVS1', 'chapter-audio-frame-magic')
        header_size, payload_size = struct.unpack('>II', prefix[4:])
        require(0 < header_size <= MAX_HEADER and payload_size <= MAX_PAYLOAD,
                'chapter-audio-frame-size')
        try:
            header = json.loads(read_exact(stream, header_size))
        except (ValueError, UnicodeError):
            raise ValueError('chapter-audio-frame-header') from None
        require(isinstance(header, dict) and header.get('request_id') == request_id,
                'chapter-audio-request-mismatch')
        if header.get('type') == 'end':
            require(payload_size == 0 and len(units) == expected_units,
                    'chapter-audio-early-end')
            ended = True; break
        require(header.get('type') == 'audio' and set(header) == {
            'type','request_id','index','total','sample_rate','sample_format','channels'},
            'chapter-audio-service-or-header-error')
        require(header['index'] == len(units) and header['total'] == expected_units,
                'chapter-audio-order-or-count')
        require(header['sample_rate'] == 24000 and header['channels'] == 1
                and header['sample_format'] == 'pcm_s16le', 'chapter-audio-format')
        require(0 < payload_size <= MAX_PAYLOAD and payload_size % 2 == 0
                and len(pcm)+payload_size <= MAX_TOTAL, 'chapter-audio-pcm-size')
        payload = read_exact(stream, payload_size); frames = payload_size//2
        require(2400 <= frames <= 1080000, 'chapter-audio-unit-duration')
        units.append(AudioUnit(len(units), samples, frames)); samples += frames
        pcm.extend(payload)
    require(ended and stream.read(1) == b'', 'chapter-audio-extra-or-missing-end')
    require(samples/24000 <= 8*60, 'chapter-audio-total-duration')
    return bytes(pcm), tuple(units)
