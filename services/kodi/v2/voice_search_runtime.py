"""Pure coordinator joining Aster's validated voice-search contracts.

Device reads, process execution and HTTP remain injected outside this object.
The coordinator deliberately stores neither credentials nor request objects.
"""
from dataclasses import dataclass, replace

from voice_capture import capture_source, parec_argv
from voice_search import (Capability, Session, VoiceUnavailable, begin, cancel,
                          captured, transcript)
from voice_search_stt import request, response


@dataclass(frozen=True)
class VoiceRuntime:
    session: Session = Session()
    sample_rate: int = 16000
    source_name: str = ''

    def start(self, capability, sources, source_name, now):
        if not isinstance(capability, Capability) or self.session.state not in (
                'idle', 'cancelled', 'error', 'results'):
            raise VoiceUnavailable('voice-runtime-start-denied')
        source = capture_source(sources, source_name)
        session = begin(self.session, capability, now)
        return replace(self, session=session, source_name=source.name), parec_argv(source)

    def accept_pcm(self, pcm, now):
        if not isinstance(pcm, bytes) or len(pcm) % 2:
            raise VoiceUnavailable('voice-runtime-audio-invalid')
        duration_ms = round(len(pcm) * 1000 / (self.sample_rate * 2))
        session = captured(self.session, len(pcm), duration_ms, now)
        return replace(self, session=session), pcm

    def speech_request(self, pcm, token):
        if self.session.state != 'transcribing':
            raise VoiceUnavailable('voice-runtime-request-denied')
        return request(pcm, token, sample_rate=self.sample_rate)

    def complete(self, status, content_type, raw):
        if self.session.state != 'transcribing':
            raise VoiceUnavailable('voice-runtime-response-denied')
        query = response(status, content_type, raw)
        return replace(self, session=transcript(self.session, query))

    def stop(self):
        return replace(self, session=cancel(self.session))
