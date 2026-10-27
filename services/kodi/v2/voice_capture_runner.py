"""Bounded in-memory recorder for an explicitly selected voice source."""
import os
import selectors
import subprocess
import time

from voice_capture import capture_source, parec_argv
from voice_search import VoiceUnavailable


MAX_BYTES = 160000
MIN_BYTES = 8000
MAXIMUM_SECONDS = 4


def record(source, *, cancelled, released, maximum_seconds=MAXIMUM_SECONDS,
           _spawn=subprocess.Popen):
    """Record until release or deadline; cancellation discards the result.

    The caller owns press-to-listen admission and passes the exact observed
    source. No default device, file, shell, logging or speech transport is used.
    The injected launcher exists for synthetic process tests without a mic.
    """
    if (not callable(cancelled) or not callable(released)
            or type(maximum_seconds) not in (int, float)
            or not .1 <= maximum_seconds <= MAXIMUM_SECONDS):
        raise VoiceUnavailable('voice-recorder-policy')
    argv = parec_argv(source)
    capture_source((source,), source.name)
    if cancelled():
        raise VoiceUnavailable('voice-recorder-cancelled')
    audio = bytearray()
    process = None
    selector = selectors.DefaultSelector()
    try:
        process = _spawn(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, shell=False, close_fds=True)
        if process.stdout is None:
            raise VoiceUnavailable('voice-recorder-pipe')
        os.set_blocking(process.stdout.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ)
        end = time.monotonic() + maximum_seconds
        while True:
            if cancelled():
                raise VoiceUnavailable('voice-recorder-cancelled')
            if process.poll() is not None:
                raise VoiceUnavailable('voice-recorder-ended')
            if released() or time.monotonic() >= end:
                break
            for key, _ in selector.select(timeout=min(.05, max(0, end-time.monotonic()))):
                chunk = os.read(key.fileobj.fileno(), min(16384, MAX_BYTES-len(audio)+1))
                if not chunk:
                    raise VoiceUnavailable('voice-recorder-ended')
                audio.extend(chunk)
                if len(audio) > MAX_BYTES:
                    raise VoiceUnavailable('voice-recorder-size')
        if cancelled():
            raise VoiceUnavailable('voice-recorder-cancelled')
        if not MIN_BYTES <= len(audio) <= MAX_BYTES or len(audio) % 2:
            raise VoiceUnavailable('voice-recorder-audio')
        result = bytes(audio)
    except OSError:
        raise VoiceUnavailable('voice-recorder-unavailable') from None
    finally:
        selector.close()
        if process is not None:
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=.5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=.5)
            finally:
                if process.stdout is not None:
                    process.stdout.close()
        audio.clear()
    if cancelled():
        raise VoiceUnavailable('voice-recorder-cancelled')
    return result
