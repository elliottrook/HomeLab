"""Credential-free wire contract for Aster voice-search STT.

The caller supplies a short-lived authorization value and an injected HTTP
transport. This module never reads a secret, opens a microphone or writes an
audio file.
"""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import re
import wave

from global_search import SearchUnavailable
from voice_search import normalize_spoken_query


class STTUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class Request:
    path: str
    headers: dict
    body: bytes
    timeout: int


TOKEN = re.compile(r'^[A-Za-z0-9._~-]{32,512}$')


def wav(pcm, *, sample_rate=16000):
    if (not isinstance(pcm, bytes) or not 8000 <= len(pcm) <= 320000
            or len(pcm) % 2 or type(sample_rate) is not int
            or sample_rate not in (16000, 24000, 48000)):
        raise STTUnavailable('voice-audio-invalid')
    duration = len(pcm) / (sample_rate * 2)
    if not .25 <= duration <= 10:
        raise STTUnavailable('voice-audio-duration')
    output = BytesIO()
    with wave.open(output, 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(pcm)
    return output.getvalue()


def request(pcm, token, *, sample_rate=16000):
    if not isinstance(token, str) or not TOKEN.fullmatch(token):
        raise STTUnavailable('voice-credential-invalid')
    audio = wav(pcm, sample_rate=sample_rate)
    boundary = 'aster-'+hashlib.sha256(audio).hexdigest()[:24]
    body = (f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="audio"; filename="voice.wav"\r\n'
            'Content-Type: audio/wav\r\n\r\n').encode()+audio+f'\r\n--{boundary}--\r\n'.encode()
    if len(body) > 15 * 1024 * 1024:
        raise STTUnavailable('voice-request-too-large')
    return Request('/v1/stt', {
        'Authorization': 'Bearer '+token,
        'Content-Type': 'multipart/form-data; boundary='+boundary,
        'Content-Length': str(len(body)),
        'Accept': 'application/json',
    }, body, 20)


def response(status, content_type, raw):
    if (status != 200 or content_type.split(';', 1)[0].strip().lower() != 'application/json'
            or not isinstance(raw, bytes) or not 1 <= len(raw) <= 16384):
        raise STTUnavailable('voice-response-invalid')
    try:
        value = json.loads(raw)
        if not isinstance(value, dict) or set(value) != {'text'}:
            raise ValueError
        query = normalize_spoken_query(value['text'])
    except (ValueError, TypeError, UnicodeError, SearchUnavailable):
        raise STTUnavailable('voice-response-invalid') from None
    if not query:
        raise STTUnavailable('voice-response-empty')
    return query
