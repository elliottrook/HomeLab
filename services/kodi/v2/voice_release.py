"""Nonblocking release signal for one admitted G20 press-to-talk session."""
import os
from pathlib import Path
import struct

from voice_search import VoiceUnavailable


PACKET = struct.Struct('llHHI')
EV_KEY = 1


class ReleaseSignal:
    def __init__(self, handler, code, *, _open=os.open):
        if (not isinstance(handler, str) or not handler.startswith('event')
                or not handler[5:].isdigit() or type(code) is not int or code != 217):
            raise VoiceUnavailable('voice-release-policy')
        try:
            self.descriptor = _open(Path('/dev/input') / handler,
                                    os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
        except OSError:
            raise VoiceUnavailable('voice-release-unavailable') from None
        self.code = code
        self.closed = False

    def released(self):
        if self.closed:
            return True
        try:
            raw = os.read(self.descriptor, PACKET.size * 16)
        except BlockingIOError:
            return False
        except OSError:
            raise VoiceUnavailable('voice-release-unavailable') from None
        if len(raw) % PACKET.size:
            raise VoiceUnavailable('voice-release-framing')
        for offset in range(0, len(raw), PACKET.size):
            _, _, event_type, code, value = PACKET.unpack(raw[offset:offset + PACKET.size])
            if event_type == EV_KEY and code == self.code and value == 0:
                return True
        return False

    def close(self):
        if not self.closed:
            os.close(self.descriptor)
            self.closed = True
