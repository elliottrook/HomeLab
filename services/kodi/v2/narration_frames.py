"""Bounded AVS1 proof decoder: measured sentence durations, no word timing."""
from dataclasses import dataclass
import json
import struct

MAX_HEADER = 4096
MAX_PAYLOAD = 2 * 1024 * 1024
MAX_TOTAL = 4 * 1024 * 1024

def require(ok, code):
    if not ok: raise ValueError(code)

@dataclass(frozen=True)
class SentenceAudio:
    index: int
    start_sample: int
    frames: int
    sample_rate: int = 24000
    @property
    def duration(self): return self.frames/self.sample_rate

def read_exact(stream, size):
    raw = bytearray()
    while len(raw) < size:
        block = stream.read(size-len(raw))
        require(bool(block), 'narration-truncated-frame')
        raw.extend(block)
    return bytes(raw)

def decode(stream, request_id, *, on_audio=None):
    units = []; pcm = bytearray(); ended = False; samples = 0
    for _ in range(3):
        prefix = read_exact(stream, 12)
        require(prefix[:4] == b'AVS1', 'narration-frame-magic')
        header_size, payload_size = struct.unpack('>II', prefix[4:])
        require(0 < header_size <= MAX_HEADER and payload_size <= MAX_PAYLOAD, 'narration-frame-size')
        try: header = json.loads(read_exact(stream, header_size))
        except (ValueError, UnicodeError): raise ValueError('narration-frame-header') from None
        require(isinstance(header, dict) and header.get('request_id') == request_id, 'narration-request-mismatch')
        if header.get('type') == 'end':
            require(payload_size == 0 and len(units) == 2, 'narration-early-end')
            ended = True; break
        require(header.get('type') == 'audio' and set(header) == {
            'type','request_id','index','total','sample_rate','sample_format','channels'}, 'narration-service-or-header-error')
        require(type(header['index']) is int and header['index'] == len(units) and
                type(header['total']) is int and header['total'] == 2, 'narration-order-or-count')
        require(type(header['sample_rate']) is int and header['sample_rate'] == 24000 and
                type(header['channels']) is int and header['channels'] == 1 and
                header['sample_format'] == 'pcm_s16le', 'narration-audio-format')
        require(0 < payload_size <= MAX_PAYLOAD and payload_size % 2 == 0 and
                len(pcm)+payload_size <= MAX_TOTAL, 'narration-pcm-size')
        payload = read_exact(stream, payload_size)
        if on_audio is not None: on_audio()
        frames = payload_size//2
        require(.1 <= frames/24000 <= 45, 'narration-unit-duration')
        units.append(SentenceAudio(len(units), samples, frames)); samples += frames; pcm.extend(payload)
    require(ended and stream.read(1) == b'', 'narration-extra-or-missing-end')
    require(samples/24000 <= 60, 'narration-total-duration')
    return bytes(pcm), tuple(units)
