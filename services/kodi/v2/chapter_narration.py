"""Exact chapter-source spans paired with measured sentence audio units.

This is sentence-level alignment only. It deliberately cannot manufacture
word timestamps from character counts or total audio duration.
"""
from dataclasses import dataclass
import hashlib
import re

MAX_TEXT = 2000
MAX_UNITS = 32

def require(ok, code):
    if not ok:
        raise ValueError(code)

@dataclass(frozen=True)
class SpokenUnit:
    index: int
    text_start: int
    text_end: int
    sample_start: int
    sample_end: int

@dataclass(frozen=True)
class ChapterPlan:
    chapter_sha256: str
    spoken_sha256: str
    audio_sha256: str
    sample_rate: int
    units: tuple

    @property
    def total_samples(self):
        return self.units[-1].sample_end

    def active(self, sample, audio_sha256):
        if type(sample) is not int or sample < 0 or audio_sha256 != self.audio_sha256:
            return None
        return next((unit for unit in self.units
                     if unit.sample_start <= sample < unit.sample_end), None)

def source(chapter, paragraph_limit=3):
    """Return exact source text and spans for a bounded linear chapter prefix."""
    require(type(paragraph_limit) is int and 1 <= paragraph_limit <= 6,
            'chapter-narration-paragraph-limit')
    paragraphs = [block for block in chapter.blocks if block.kind == 'paragraph'][:paragraph_limit]
    require(len(paragraphs) == paragraph_limit, 'chapter-narration-paragraphs')
    spoken = ' '.join(block.text for block in paragraphs)
    require(0 < len(spoken) <= MAX_TEXT, 'chapter-narration-text-size')
    units = []
    cursor = 0
    for sentence in re.split(r'(?<=[.!?])\s+', spoken):
        sentence = sentence.strip()
        if not sentence:
            continue
        require(len(sentence) <= 240, 'chapter-narration-unit-size')
        local = spoken.find(sentence, cursor)
        require(local >= cursor, 'chapter-narration-source-order')
        chapter_start = chapter.text.find(sentence, paragraphs[0].offset)
        require(chapter_start >= paragraphs[0].offset, 'chapter-narration-source-span')
        units.append((sentence, chapter_start, chapter_start + len(sentence)))
        cursor = local + len(sentence)
    require(2 <= len(units) <= MAX_UNITS, 'chapter-narration-unit-count')
    return spoken, tuple(units)

def build(chapter, measurements, audio_sha256, expected_spoken_sha256,
          paragraph_limit=3):
    spoken, source_units = source(chapter, paragraph_limit)
    require(hashlib.sha256(spoken.encode()).hexdigest() == expected_spoken_sha256,
            'chapter-narration-text-identity')
    require(isinstance(audio_sha256, str) and re.fullmatch('[a-f0-9]{64}', audio_sha256),
            'chapter-narration-audio-identity')
    require(len(measurements) == len(source_units), 'chapter-narration-measurement-count')
    result = []
    sample = 0
    for index, ((text, start, end), measurement) in enumerate(zip(source_units, measurements)):
        require(type(measurement) is dict and measurement.get('index') == index
                and measurement.get('start_sample') == sample
                and type(measurement.get('frames')) is int
                and 2400 <= measurement['frames'] <= 1080000
                and measurement.get('sample_rate', 24000) == 24000,
                'chapter-narration-measurement-invalid')
        result.append(SpokenUnit(index, start, end, sample,
                                 sample + measurement['frames']))
        sample += measurement['frames']
    return ChapterPlan(chapter.chapter_sha256, expected_spoken_sha256,
                       audio_sha256, 24000, tuple(result))
