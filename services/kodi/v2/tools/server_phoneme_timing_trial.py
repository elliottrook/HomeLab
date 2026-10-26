"""One bounded native Kokoro timing trial over repository synthetic text.

Run only on Aster Speech after approval. It invokes the unchanged local model
once, writes private evidence, and never reads a real book or changes a service.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import wave

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, '/opt/aster-voice-candidate')
from phoneme_word_alignment import TimedPhoneme, align_phonemes

TEXT = ('Mara reached the lantern house just before the rain. '
        'From the road it had looked small, almost an afterthought beside the hill, '
        'but the doorway was tall enough to hold the last light of the evening.')
TEXT_SHA = '3e8099be742e6ffad165a3b8de53ee0ed59c4add60aed0c468cda767bfeb21c8'
CHECKPOINT = Path('/var/lib/aster-speech/aster-reader-phoneme-timing-20261026')
SERVICE = 'aster-voice-candidate.service'


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def save(name, value):
    raw = value if isinstance(value, bytes) else (
        json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(str(CHECKPOINT / name),
                 os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def service_pid():
    value = int(subprocess.check_output(
        ['systemctl', 'show', SERVICE, '-p', 'MainPID', '--value'], timeout=3))
    require(value > 1, 'phoneme-timing-service-not-running')
    return value


def main():
    os.umask(0o077); os.nice(10)
    require(os.uname().nodename == 'aster-speech' and os.geteuid() == 0
            and len(sys.argv) == 1, 'phoneme-timing-speech-host-only')
    require(hashlib.sha256(TEXT.encode()).hexdigest() == TEXT_SHA,
            'phoneme-timing-text-drift')
    before = service_pid()
    CHECKPOINT.mkdir(mode=0o700, exist_ok=False)
    save('attempt.json', dict(synthetic=True, text_sha256=TEXT_SHA,
         voice='bm_daniel', language='en-gb', speed=.95, invocations=1,
         real_book_access=False, service_change=False, network=False))
    result = dict(passed=False, synthetic=True, model_invocations=0,
                  network=False, service_changed=False, evidence_private=True)
    worker = None
    started = time.monotonic()
    try:
        from kokoro_candidate import (KokoroWorker, LANGUAGE, SPEED, VOICE,
                                      verify_assets)
        require((VOICE, LANGUAGE, SPEED) == ('bm_daniel', 'en-gb', .95),
                'phoneme-timing-voice-policy')
        verify_assets()
        worker = KokoroWorker()
        phonemes = ' '.join(worker._engine.tokenizer.phonemize(TEXT, LANGUAGE).split())
        require(phonemes and len(phonemes) <= 4000,
                'phoneme-timing-plan-size')
        result['model_invocations'] = 1
        audio, sample_rate, values = worker._engine.create_timed(
            phonemes, voice=VOICE, speed=SPEED, lang=LANGUAGE,
            is_phonemes=True, continuous=False)
        require(sample_rate == 24000 and len(audio) > sample_rate,
                'phoneme-timing-audio-format')
        duration = len(audio) / sample_rate
        measured = tuple(TimedPhoneme(value.phoneme, value.start, value.end)
                         for value in values)
        pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype('<i2', copy=False)
        with wave.open(str(CHECKPOINT / 'sample.wav'), 'wb') as output:
            output.setnchannels(1); output.setsampwidth(2)
            output.setframerate(sample_rate); output.writeframes(pcm.tobytes())
        os.chmod(CHECKPOINT / 'sample.wav', 0o600)
        save('timings-private.json', [dict(phoneme=value.phoneme,
             start=value.start, end=value.end) for value in measured])
        save('plan-private.json', dict(text=TEXT, phonemes=phonemes))
        audio_sha = hashlib.sha256((CHECKPOINT/'sample.wav').read_bytes()).hexdigest()
        result.update(phoneme_count=len(measured), duration_seconds=round(duration, 3),
                      audio_sha256=audio_sha, diagnostic_capture_complete=True)
        cues = align_phonemes(TEXT, phonemes, measured, duration)
        require(len(cues) == len(re.findall(r"[^\W_]+(?:[’'\-][^\W_]+)*", TEXT)),
                'phoneme-timing-word-coverage')
        save('cues-private.json', [cue.__dict__ for cue in cues])
        elapsed = time.monotonic() - started
        require(elapsed <= 180, 'phoneme-timing-time-budget')
        result.update(passed=True, word_count=len(cues), exact_coverage=True,
                      elapsed_seconds=round(elapsed, 3))
    except Exception as error:
        code = str(error)
        result['code'] = code if re.fullmatch(r'[a-z0-9-]{1,100}', code) else type(error).__name__
        result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    finally:
        if worker is not None:
            worker.close()
        result['service_pid_unchanged'] = service_pid() == before
        save('proof.json', result)
        print(json.dumps({key: result.get(key) for key in
              ('passed', 'code', 'word_count', 'phoneme_count', 'duration_seconds',
               'elapsed_seconds', 'service_pid_unchanged') if key in result}, sort_keys=True))


if __name__ == '__main__':
    main()
