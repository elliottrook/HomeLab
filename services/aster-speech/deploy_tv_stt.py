#!/usr/bin/env python3
"""Transactional source-local activation of the STT-only Aster TV identity."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import wave


SOURCE = Path('/opt/aster-speech/aster_speech.py')
ENV = Path('/etc/aster-speech/speech.env')
KEY = Path('/etc/aster-speech/tv-stt.key')
CHECKPOINT = Path('/var/lib/aster-speech/checkpoints/tv-stt-20261026')
EXPECTED_BEFORE = '1eb8d326ddbc87aee4ae74f28fdab8bf0c5feeb3e7e5f8fd016ddf2dbf0836f5'
BASE = 'http://192.168.70.14:9130'


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=180, check=True)


def atomic(path, raw, mode):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-tv-stt-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def request(path, *, token=None, body=None, content_type=None):
    headers = {}
    if token: headers['Authorization'] = 'Bearer ' + token
    if content_type: headers['Content-Type'] = content_type
    value = urllib.request.Request(BASE + path, data=body, headers=headers,
                                   method='POST' if body is not None else 'GET')
    try:
        with urllib.request.urlopen(value, timeout=30) as reply:
            return reply.status, reply.headers.get_content_type(), reply.read(16385)
    except urllib.error.HTTPError as error:
        return error.code, error.headers.get_content_type(), error.read(16385)


def silent_wav():
    output = tempfile.SpooledTemporaryFile(max_size=64000)
    with wave.open(output, 'wb') as stream:
        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000)
        stream.writeframes(b'\0\0' * 8000)
    output.seek(0); return output.read()


def main(stage):
    stage = Path(stage).resolve()
    candidate = stage / 'aster_speech.py'
    tests = stage / 'test_aster_speech.py'
    staged_key = stage / 'tv-stt.key'
    require(os.geteuid() == 0 and SOURCE.is_file() and ENV.is_file(), 'speech-host-policy')
    require(digest(SOURCE) == EXPECTED_BEFORE and not KEY.exists()
            and not CHECKPOINT.exists(), 'speech-predecessor-drift')
    require(candidate.is_file() and tests.is_file() and staged_key.is_file()
            and not any(path.is_symlink() for path in (candidate, tests, staged_key)),
            'speech-stage-members')
    metadata = staged_key.stat()
    require(metadata.st_uid == 0 and stat.S_IMODE(metadata.st_mode) == 0o600
            and 32 <= metadata.st_size <= 513, 'speech-key-custody')
    run('/opt/aster-speech/venv/bin/python', str(tests), '-q')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(SOURCE, CHECKPOINT / 'aster_speech.py')
    shutil.copy2(ENV, CHECKPOINT / 'speech.env')
    os.chmod(CHECKPOINT / 'speech.env', 0o600)
    try:
        atomic(SOURCE, candidate.read_bytes(), 0o644)
        shutil.copy2(staged_key, KEY)
        shutil.chown(KEY, user='root', group='aster-speech'); KEY.chmod(0o640)
        env = ENV.read_text()
        require('ASTER_SPEECH_TV_STT_KEY_FILE' not in env, 'speech-env-already-scoped')
        atomic(ENV, (env.rstrip() + '\nASTER_SPEECH_TV_STT_KEY_FILE=/etc/aster-speech/tv-stt.key\n').encode(), 0o640)
        shutil.chown(ENV, user='root', group='aster-speech')
        run('/usr/bin/systemctl', 'restart', 'aster-speech.service')
        require(run('/usr/bin/systemctl', 'is-active', 'aster-speech.service').stdout.strip() == 'active',
                'speech-service-inactive')
        status, _, raw = request('/health')
        require(status == 200 and json.loads(raw).get('status') == 'ok', 'speech-health')
        token = KEY.read_text(encoding='ascii').strip()
        audio = silent_wav(); boundary = 'aster-tv-stt-validation'
        body = (('--' + boundary + '\r\nContent-Disposition: form-data; name="audio"; filename="test.wav"\r\n'
                 'Content-Type: audio/wav\r\n\r\n').encode() + audio
                + ('\r\n--' + boundary + '--\r\n').encode())
        status, content_type, raw = request('/v1/stt', token=token, body=body,
                                            content_type='multipart/form-data; boundary=' + boundary)
        require(status == 200 and content_type == 'application/json'
                and set(json.loads(raw)) == {'text'}, 'speech-scoped-stt')
        status, _, _ = request('/v1/tts', token=token, body=b'{"text":"not authorized"}',
                               content_type='application/json')
        require(status == 401, 'speech-scoped-key-broadened')
    except Exception:
        atomic(SOURCE, (CHECKPOINT / 'aster_speech.py').read_bytes(), 0o644)
        atomic(ENV, (CHECKPOINT / 'speech.env').read_bytes(), 0o640)
        shutil.chown(ENV, user='root', group='aster-speech')
        if KEY.exists(): KEY.unlink()
        run('/usr/bin/systemctl', 'restart', 'aster-speech.service')
        raise
    print(json.dumps({'installed': True, 'source_sha256': digest(SOURCE),
                      'checkpoint': str(CHECKPOINT), 'stt_only_verified': True},
                     sort_keys=True))


if __name__ == '__main__':
    require(len(sys.argv) == 2, 'speech-stage-argument')
    main(sys.argv[1])
