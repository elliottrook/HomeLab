#!/usr/bin/env python3
"""Transactionally select the already-cached small English STT model."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request


ENV = Path('/etc/aster-speech/speech.env')
CACHE = Path('/root/.cache/huggingface/hub/models--Systran--faster-whisper-small.en')
CHECKPOINT = Path('/var/lib/aster-speech/checkpoints/small-en-title-search-20261027')
BEFORE = 'b087ca9ade7d8c2741e9fcff835a82db9037f669673061525fba475eb92d0c25'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=60, check=True)


def health():
    try:
        with urllib.request.urlopen('http://192.168.70.14:9130/health', timeout=3) as response:
            return response.status == 200 and b'"status":"ok"' in response.read(1024)
    except OSError:
        return False


def atomic(path, raw, mode):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-stt-model-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        descriptor = None
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except Exception:
        try:
            if descriptor is not None:
                os.close(descriptor)
        except OSError:
            pass
        Path(temporary).unlink(missing_ok=True)
        raise


def main():
    require(os.uname().nodename == 'aster-speech', 'speech-lxc-only')
    require(ENV.is_file() and not ENV.is_symlink() and digest(ENV) == BEFORE,
            'environment-drift')
    require(CACHE.is_dir() and not CHECKPOINT.exists(), 'model-or-checkpoint')
    raw = ENV.read_bytes()
    before = b'ASTER_SPEECH_STT_MODEL=base.en\n'
    after = b'ASTER_SPEECH_STT_MODEL=small.en\n'
    require(raw.count(before) == 1 and after not in raw, 'model-setting-drift')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(ENV, CHECKPOINT / ENV.name)
    try:
        atomic(ENV, raw.replace(before, after), 0o640)
        shutil.chown(ENV, user='root', group='aster-speech')
        run('/usr/bin/systemctl', 'restart', 'aster-speech')
        end = time.monotonic() + 60
        while time.monotonic() < end and not health():
            time.sleep(.5)
        require(health(), 'health-failed')
        require(run('/usr/bin/systemctl', 'is-active', 'aster-speech').stdout.strip()
                == 'active', 'service-inactive')
    except Exception:
        try:
            shutil.copy2(CHECKPOINT / ENV.name, ENV)
            run('/usr/bin/systemctl', 'restart', 'aster-speech')
        finally:
            raise
    print('small-en-stt-active checkpoint=' + str(CHECKPOINT))


if __name__ == '__main__':
    main()
