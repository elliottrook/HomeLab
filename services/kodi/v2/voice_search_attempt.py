"""One explicitly admitted voice attempt; no hardware registration or HTTP.

The owner supplies cancellation/release signals, the scoped token supplier and
the bounded speech transport. Nothing retries. Audio and credentials are local
to this call; the returned state contains only the normalized search query.
"""
from dataclasses import replace
import time

from voice_capture import capture_source
from voice_capture_runner import record
from voice_search import Session, VoiceUnavailable
from voice_search_runtime import VoiceRuntime
from voice_search_stt import STTUnavailable
from voice_search_ui import present


def attempt(capability, sources, source_name, *, cancelled, released,
            token, transport, changed, recorder=record, clock=time.monotonic):
    if not all(callable(value) for value in
               (cancelled, released, token, transport, changed, recorder, clock)):
        raise VoiceUnavailable('voice-attempt-callbacks')
    runtime = VoiceRuntime()

    def publish():
        changed(present(capability, runtime.session))

    def cancel_if_needed():
        nonlocal runtime
        if cancelled():
            if runtime.session.state in ('listening', 'transcribing'):
                runtime = runtime.stop()
            else:
                runtime = replace(runtime, session=Session('cancelled', reason='Cancelled'))
            publish()
            return True
        return False

    if cancel_if_needed():
        return runtime.session
    try:
        runtime, _ = runtime.start(capability, sources, source_name, clock())
        source = capture_source(sources, source_name)
        publish()
        pcm = recorder(source, cancelled=cancelled, released=released)
        if cancel_if_needed():
            return runtime.session
        runtime, pcm = runtime.accept_pcm(pcm, clock())
        publish()
        if cancel_if_needed():
            return runtime.session
        credential = token()
        try:
            wire = runtime.speech_request(pcm, credential)
        finally:
            credential = None
            pcm = None
        if cancel_if_needed():
            return runtime.session
        try:
            status, content_type, raw = transport(wire, cancelled=cancelled)
        finally:
            wire = None
        if cancel_if_needed():
            return runtime.session
        runtime = runtime.complete(status, content_type, raw)
        raw = None
        publish()
    except (VoiceUnavailable, STTUnavailable, OSError, TimeoutError):
        if not cancel_if_needed():
            runtime = replace(runtime, session=Session(
                'error', reason='Voice search unavailable · use the keyboard or try again'))
            publish()
    return runtime.session
