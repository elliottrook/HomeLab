"""Sample-exact sentence mapping. Never invents per-word speech timestamps."""
from dataclasses import dataclass
import hashlib
import re
from narration_frames import SentenceAudio

@dataclass(frozen=True)
class SentenceSpan:
    text_start: int
    text_end: int
    sample_start: int
    sample_end: int

@dataclass(frozen=True)
class SentencePlan:
    text_sha256: str
    audio_sha256: str
    sample_rate: int
    sentences: tuple
    @property
    def total_samples(self): return self.sentences[-1].sample_end
    def active(self, sample, audio_sha256):
        if type(sample) is not int or sample < 0 or audio_sha256 != self.audio_sha256:
            return None
        return next((s for s in self.sentences if s.sample_start <= sample < s.sample_end), None)

def build(text, sentences, units, audio_sha256, expected_text_sha256):
    if (not isinstance(text,str) or not text or len(text)>2000 or len(sentences)!=2 or len(units)!=2
            or not all(isinstance(s,str) and s and len(s)<=240 for s in sentences)
            or ' '.join(sentences)!=text):
        raise ValueError('narration-source-not-exact')
    text_hash=hashlib.sha256(text.encode()).hexdigest()
    if text_hash!=expected_text_sha256 or not isinstance(audio_sha256,str) or not re.fullmatch('[a-f0-9]{64}',audio_sha256):
        raise ValueError('narration-content-identity')
    spans=[];offset=0;sample=0
    for index,(sentence,unit) in enumerate(zip(sentences,units)):
        if (not isinstance(unit,SentenceAudio) or type(unit.index) is not int or unit.index!=index
                or type(unit.start_sample) is not int or unit.start_sample!=sample
                or type(unit.frames) is not int or not 2400<=unit.frames<=1080000
                or type(unit.sample_rate) is not int or unit.sample_rate!=24000):
            raise ValueError('narration-measurement-invalid')
        spans.append(SentenceSpan(offset,offset+len(sentence),sample,sample+unit.frames))
        offset+=len(sentence)+1;sample+=unit.frames
    return SentencePlan(text_hash,audio_sha256,24000,tuple(spans))
