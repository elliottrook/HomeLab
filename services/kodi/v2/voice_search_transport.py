"""Restricted HP transport for Aster voice-search STT.

The endpoint, route and credential location are fixed.  There are no redirects,
retries, URL discovery, TTS routes or transcript/audio logs.
"""
import http.client
import os
from pathlib import Path
import re
import stat

from voice_search_stt import Request, STTUnavailable


HOST = '192.168.70.14'
PORT = 9130
PATH = '/v1/stt'
KEY_PATH = Path('/storage/.aster-secrets/voice-stt.key')
TOKEN = re.compile(r'^[A-Za-z0-9._~-]{32,512}$')
MAX_RESPONSE = 16384


def credential(path=KEY_PATH, *, expected_uid=0):
    path = Path(path)
    try:
        metadata = path.lstat()
        if (not path.is_absolute() or path.is_symlink()
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != expected_uid
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_size > 513):
            raise STTUnavailable('voice-credential-custody')
        value = path.read_text(encoding='ascii').strip()
    except (OSError, UnicodeError):
        raise STTUnavailable('voice-credential-unavailable') from None
    if not TOKEN.fullmatch(value):
        raise STTUnavailable('voice-credential-invalid')
    return value


def transport(wire, *, cancelled, _connection=http.client.HTTPConnection):
    if (not isinstance(wire, Request) or wire.path != PATH
            or not callable(cancelled) or cancelled()):
        raise STTUnavailable('voice-transport-policy')
    connection = _connection(HOST, PORT, timeout=wire.timeout)
    try:
        connection.request('POST', PATH, body=wire.body, headers=wire.headers)
        if cancelled():
            raise STTUnavailable('voice-transport-cancelled')
        reply = connection.getresponse()
        raw = reply.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE or cancelled():
            raise STTUnavailable('voice-transport-response')
        return reply.status, reply.getheader('Content-Type', ''), raw
    except (OSError, http.client.HTTPException, TimeoutError):
        raise STTUnavailable('voice-transport-unavailable') from None
    finally:
        connection.close()
