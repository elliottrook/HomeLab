"""Validate already-captured synthetic Kokoro timings without synthesis."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import wave

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from phoneme_word_alignment import TimedPhoneme, align_phoneme_groups

CHECKPOINT = Path('/var/lib/aster-speech/aster-reader-phoneme-timing-diagnostic2-20261026')
TEXT_SHA = '3e8099be742e6ffad165a3b8de53ee0ed59c4add60aed0c468cda767bfeb21c8'
SOURCE_GROUP_SIZES = (1, 1, 1, 1, 1, 1, 1, 1, 1, 2,
                      1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                      1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                      1, 1, 2, 1)


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def main():
    os.umask(0o077)
    require(os.uname().nodename == 'aster-speech' and os.geteuid() == 0
            and len(sys.argv) == 1, 'phoneme-validation-speech-host-only')
    plan = json.loads((CHECKPOINT/'plan-private.json').read_text())
    raw = json.loads((CHECKPOINT/'timings-private.json').read_text())
    proof = json.loads((CHECKPOINT/'proof.json').read_text())
    require(hashlib.sha256(plan['text'].encode()).hexdigest() == TEXT_SHA,
            'phoneme-validation-text-drift')
    require(proof.get('model_invocations') == 1
            and proof.get('diagnostic_capture_complete') is True
            and proof.get('service_pid_unchanged') is True,
            'phoneme-validation-source-proof')
    with wave.open(str(CHECKPOINT/'sample.wav'), 'rb') as audio:
        require((audio.getnchannels(), audio.getsampwidth(), audio.getframerate())
                == (1, 2, 24000), 'phoneme-validation-audio-format')
        duration = audio.getnframes() / audio.getframerate()
    values = tuple(TimedPhoneme(value['phoneme'], value['start'], value['end'])
                   for value in raw)
    cues = align_phoneme_groups(plan['text'], plan['phonemes'], values, duration,
                                SOURCE_GROUP_SIZES)
    result = dict(passed=True, synthetic=True, model_invocations=0,
                  source_model_invocations=1, service_change=False, network=False,
                  source_word_count=sum(SOURCE_GROUP_SIZES),
                  spoken_group_count=len(cues), phoneme_count=len(values),
                  silent_zero_count=sum(value.start == value.end for value in values),
                  duration_seconds=round(duration, 3), exact_coverage=True,
                  text_sha256=TEXT_SHA)
    payload = (json.dumps(result, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(str(CHECKPOINT/'validation.json'),
                 os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(payload); output.flush(); os.fsync(output.fileno())
    print(json.dumps({key: result[key] for key in
          ('passed', 'source_word_count', 'spoken_group_count', 'phoneme_count', 'silent_zero_count',
           'duration_seconds', 'model_invocations')}, sort_keys=True))


if __name__ == '__main__':
    main()
