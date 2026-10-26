"""Build an exact Reader timeline from a validated native timing fixture."""
from dataclasses import dataclass
import hashlib
import re

from chapter_narration import SpokenUnit
from word_alignment import WORD

MAX_GROUPS = 4000


def require(ok, code):
    if not ok:
        raise ValueError(code)


@dataclass(frozen=True)
class WordGroupPlan:
    chapter_sha256: str
    source_sha256: str
    audio_sha256: str
    sample_rate: int
    audio_frames: int
    units: tuple

    @property
    def total_samples(self):
        return self.audio_frames

    def active(self, sample, audio_sha256):
        if type(sample) is not int or sample < 0 or audio_sha256 != self.audio_sha256:
            return None
        return next((unit for unit in self.units
                     if unit.sample_start <= sample < unit.sample_end), None)


def _source(chapter, wanted):
    """Find the unique sentence-boundary prefix pinned by ``wanted``."""
    candidates = []
    for block in chapter.blocks:
        if block.kind != 'paragraph':
            continue
        for boundary in re.finditer(r'(?<=[.!?])(?:\s+|$)', block.text):
            text = block.text[:boundary.start()].rstrip()
            if hashlib.sha256(text.encode()).hexdigest() == wanted:
                candidates.append((block.offset, text))
    require(len(candidates) == 1, 'word-group-source-identity')
    return candidates[0]


def build(chapter, fixture, audio_sha256):
    required = {'schema', 'synthetic', 'source_sha256', 'audio_sha256',
                'sample_rate', 'audio_frames', 'source_word_count',
                'spoken_group_count', 'cues'}
    require(type(fixture) is dict and set(fixture) == required,
            'word-group-fixture-schema')
    require(fixture['schema'] == 1 and fixture['synthetic'] is True
            and fixture['audio_sha256'] == audio_sha256,
            'word-group-fixture-identity')
    require(fixture['sample_rate'] == 24000
            and type(fixture['audio_frames']) is int
            and fixture['audio_frames'] > 24000,
            'word-group-audio-shape')
    offset, source = _source(chapter, fixture['source_sha256'])
    words = tuple(WORD.finditer(source))
    cues = fixture['cues']
    require(type(cues) is list and 0 < len(cues) <= MAX_GROUPS
            and fixture['source_word_count'] == len(words)
            and fixture['spoken_group_count'] == len(cues),
            'word-group-count')

    units = []
    word_cursor = 0
    previous_sample = 0
    for index, cue in enumerate(cues):
        require(type(cue) is dict and set(cue) == {
            'start_character', 'end_character', 'start_sample', 'end_sample'},
            'word-group-cue-schema')
        start = cue['start_character']; end = cue['end_character']
        sample_start = cue['start_sample']; sample_end = cue['end_sample']
        require(all(type(value) is int for value in (start, end, sample_start, sample_end))
                and 0 <= start < end <= len(source)
                and previous_sample <= sample_start < sample_end <= fixture['audio_frames'],
                'word-group-cue-range')
        require(word_cursor < len(words) and words[word_cursor].start() == start,
                'word-group-source-order')
        width = 0
        while word_cursor + width < len(words) and words[word_cursor + width].end() <= end:
            width += 1
        require(1 <= width <= 4 and words[word_cursor + width - 1].end() == end,
                'word-group-source-span')
        units.append(SpokenUnit(index, offset + start, offset + end,
                                sample_start, sample_end))
        word_cursor += width; previous_sample = sample_end
    require(word_cursor == len(words), 'word-group-source-coverage')
    return WordGroupPlan(chapter.chapter_sha256, fixture['source_sha256'],
                         audio_sha256, 24000, fixture['audio_frames'], tuple(units))
