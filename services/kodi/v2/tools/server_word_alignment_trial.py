"""One bounded local Whisper timing trial over the existing synthetic chapter.

Run only on Aster Speech after a separate operational approval.  It performs no
TTS request and permits no model download; all output stays in a new private
checkpoint on that guest.
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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from chapter_narration import source
from epub_chapter import chapter
from epub_fixture import build_readalong
from word_alignment import TimedWord, align_exact

SOURCE = Path('/var/lib/aster-speech/aster-reader-epub-chapter-20261026/chapter.wav')
CHECKPOINT = Path('/var/lib/aster-speech/aster-reader-word-alignment-20261026')
AUDIO_SHA = 'd10997803ee99ae85f06545ab5b0bad71e91906735f4811c2119a632399de02b'
SPOKEN_SHA = '70801db5b3f53de7badb7250fcc77664a7221af33f4b304d788b0c3f3b87bab9'
SERVICE = 'aster-speech.service'


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def save(name, value):
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    fd = os.open(str(CHECKPOINT / name), os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def service_pid():
    raw = subprocess.check_output(
        ['systemctl', 'show', SERVICE, '-p', 'MainPID', '--value'], timeout=3)
    value = int(raw)
    require(value > 1, 'word-alignment-service-not-running')
    return value


def allowed_environment(pid):
    values = dict(part.split(b'=', 1) for part in
                  Path('/proc/' + str(pid) + '/environ').read_bytes().split(b'\0') if b'=' in part)
    model = values.get(b'ASTER_SPEECH_STT_MODEL', b'base.en').decode()
    cache = values.get(b'HF_HOME', b'').decode()
    values.clear()
    require(re.fullmatch(r'[A-Za-z0-9._-]{1,80}', model) is not None,
            'word-alignment-model-name')
    require(cache.startswith('/') and len(cache) <= 240, 'word-alignment-cache-path')
    return model, cache


def main():
    os.umask(0o077)
    os.nice(10)
    require(os.uname().nodename == 'aster-speech' and len(sys.argv) == 1,
            'word-alignment-speech-host-only')
    require(SOURCE.is_file() and not SOURCE.is_symlink(), 'word-alignment-source-audio')
    raw = SOURCE.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == AUDIO_SHA, 'word-alignment-audio-drift')
    with wave.open(str(SOURCE), 'rb') as wav:
        require((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) == (1, 2, 24000),
                'word-alignment-audio-format')
        duration = wav.getnframes() / wav.getframerate()
    book = chapter(build_readalong())
    spoken, units = source(book)
    require(hashlib.sha256(spoken.encode()).hexdigest() == SPOKEN_SHA and len(units) == 14,
            'word-alignment-text-drift')

    before_pid = service_pid()
    model_name, cache = allowed_environment(before_pid)
    CHECKPOINT.mkdir(mode=0o700, exist_ok=False)
    save('attempt.json', dict(audio_sha256=AUDIO_SHA, spoken_sha256=SPOKEN_SHA,
         duration_seconds=duration, model=model_name, local_files_only=True,
         word_timestamps=True, tts_requests=0))
    result = dict(passed=False, synthetic=True, tts_requests=0, network=False,
                  service_changed=False, transcript_private=True)
    started = time.monotonic()
    try:
        os.environ['HF_HOME'] = cache
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device='cpu', compute_type='int8',
                             cpu_threads=2, num_workers=1, local_files_only=True)
        segments, info = model.transcribe(str(SOURCE), beam_size=1, language='en',
            word_timestamps=True, vad_filter=False, condition_on_previous_text=False)
        measured = []
        private = []
        for segment in segments:
            for value in segment.words or ():
                measured.append(TimedWord(value.word, value.start, value.end))
                private.append(dict(text=value.word, start=value.start, end=value.end,
                                    probability=value.probability))
        save('recognizer-private.json', private)
        cues = align_exact(spoken, measured, duration)
        save('cues-private.json', [cue.__dict__ for cue in cues])
        result.update(passed=True, word_count=len(cues), exact_coverage=True,
                      language=getattr(info, 'language', None),
                      elapsed_seconds=round(time.monotonic() - started, 3))
        require(result['elapsed_seconds'] <= 180, 'word-alignment-time-budget')
    except Exception as error:
        code = str(error)
        result['code'] = code if re.fullmatch(r'[a-z0-9-]{1,100}', code) else type(error).__name__
        result['measured_word_count'] = len(locals().get('measured', ()))
        result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    finally:
        result['service_pid_unchanged'] = service_pid() == before_pid
        save('proof.json', result)
        print(json.dumps({key: result.get(key) for key in
              ('passed', 'code', 'measured_word_count', 'word_count',
               'elapsed_seconds', 'service_pid_unchanged') if key in result}, sort_keys=True))


if __name__ == '__main__':
    main()
