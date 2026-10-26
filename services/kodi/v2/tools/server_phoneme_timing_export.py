"""Export a sanitized synthetic Reader fixture from validated private evidence."""
import hashlib
import json
import os
from pathlib import Path
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
            and len(sys.argv) == 1, 'phoneme-export-speech-host-only')
    validation = json.loads((CHECKPOINT/'validation.json').read_text())
    require(validation.get('passed') is True and validation.get('exact_coverage') is True
            and validation.get('model_invocations') == 0,
            'phoneme-export-validation')
    plan = json.loads((CHECKPOINT/'plan-private.json').read_text())
    require(hashlib.sha256(plan['text'].encode()).hexdigest() == TEXT_SHA,
            'phoneme-export-text-drift')
    raw = json.loads((CHECKPOINT/'timings-private.json').read_text())
    values = tuple(TimedPhoneme(value['phoneme'], value['start'], value['end'])
                   for value in raw)
    audio_path = CHECKPOINT/'sample.wav'
    with wave.open(str(audio_path), 'rb') as audio:
        sample_rate = audio.getframerate(); frames = audio.getnframes()
        require((audio.getnchannels(), audio.getsampwidth(), sample_rate)
                == (1, 2, 24000), 'phoneme-export-audio-format')
    cues = align_phoneme_groups(plan['text'], plan['phonemes'], values,
                                frames/sample_rate, SOURCE_GROUP_SIZES)
    fixture = dict(schema=1, synthetic=True, source_sha256=TEXT_SHA,
                   audio_sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
                   sample_rate=sample_rate, audio_frames=frames,
                   source_word_count=sum(SOURCE_GROUP_SIZES),
                   spoken_group_count=len(cues),
                   cues=[dict(start_character=cue.start_character,
                              end_character=cue.end_character,
                              start_sample=round(cue.start_seconds*sample_rate),
                              end_sample=round(cue.end_seconds*sample_rate))
                         for cue in cues])
    payload = (json.dumps(fixture, sort_keys=True, indent=2) + '\n').encode()
    target = CHECKPOINT/'reader-fixture.json'
    fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as output:
        output.write(payload); output.flush(); os.fsync(output.fileno())
    print(json.dumps(dict(passed=True, spoken_group_count=len(cues),
          source_word_count=sum(SOURCE_GROUP_SIZES), fixture_sha256=hashlib.sha256(payload).hexdigest()),
          sort_keys=True))


if __name__ == '__main__':
    main()
