#!/usr/bin/env python3
"""Transactional successor restoring low-latency STT after accuracy trial."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request


STAGE = Path('/tmp/aster-speech-title-latency')
SOURCE = Path('/opt/aster-speech/aster_speech.py')
CHECKPOINT = Path('/var/lib/aster-speech/checkpoints/title-search-latency-20261027')
BEFORE = '04003d550b5bda94f94658f1acf3d5078ce49386fe151c1ed1709087e0d12820'


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


def main():
    candidate = STAGE / 'aster_speech.py'
    tests = STAGE / 'test_aster_speech.py'
    require(os.uname().nodename == 'aster-speech', 'speech-lxc-only')
    require(SOURCE.is_file() and not SOURCE.is_symlink() and digest(SOURCE) == BEFORE,
            'predecessor-drift')
    require(candidate.is_file() and tests.is_file(), 'stage-incomplete')
    require(not CHECKPOINT.exists(), 'checkpoint-exists')
    run('/opt/aster-speech/venv/bin/python', str(tests))
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(SOURCE, CHECKPOINT / SOURCE.name)
    try:
        temporary = SOURCE.with_name('.aster_speech.title-latency-new')
        shutil.copy2(candidate, temporary)
        os.replace(temporary, SOURCE)
        run('/usr/bin/systemctl', 'restart', 'aster-speech')
        end = time.monotonic() + 45
        while time.monotonic() < end and not health():
            time.sleep(.5)
        require(health(), 'health-failed')
        require(run('/usr/bin/systemctl', 'is-active', 'aster-speech').stdout.strip()
                == 'active', 'service-inactive')
        require(digest(SOURCE) == digest(candidate), 'installed-drift')
    except Exception:
        try:
            shutil.copy2(CHECKPOINT / SOURCE.name, SOURCE)
            run('/usr/bin/systemctl', 'restart', 'aster-speech')
        finally:
            raise
    print('title-search-low-latency-active checkpoint=' + str(CHECKPOINT))


if __name__ == '__main__':
    main()
