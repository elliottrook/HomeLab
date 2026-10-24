"""Remote scrub preview: pure arithmetic, no playback or persistence."""
from dataclasses import dataclass,replace
import re
from music_queue import QueueSnapshot


@dataclass(frozen=True)
class ScrubPreview:
    queue_fingerprint:str
    song_id:int
    index:int
    duration_ms:int
    target_ms:int

    def __post_init__(self):
        if (not isinstance(self.queue_fingerprint,str) or not re.fullmatch(r'[0-9a-f]{64}',self.queue_fingerprint)
                or type(self.song_id) is not int or self.song_id<1
                or type(self.index) is not int or not 0<=self.index<20000
                or type(self.duration_ms) is not int or not 1000<=self.duration_ms<=604799999
                or type(self.target_ms) is not int or not 0<=self.target_ms<=self.duration_ms-1000):
            raise ValueError('invalid-scrub-preview')

    @classmethod
    def start(cls,snapshot,duration_ms,elapsed_ms):
        if (not isinstance(snapshot,QueueSnapshot) or snapshot.current_index is None
                or len(snapshot.song_ids)>20000 or type(duration_ms) is not int or duration_ms<1000
                or type(elapsed_ms) is not int or not 0<=elapsed_ms<duration_ms):
            raise ValueError('invalid-scrub-preview')
        return cls(snapshot.fingerprint,snapshot.song_ids[snapshot.current_index],snapshot.current_index,
                   duration_ms,min(elapsed_ms,duration_ms-1000))

    def adjust(self,direction):
        if type(direction) is not int or direction not in (-1,1):raise ValueError('invalid-scrub-direction')
        return replace(self,target_ms=max(0,min(self.duration_ms-1000,self.target_ms+direction*5000)))

    @property
    def percentage(self):return self.target_ms/self.duration_ms*100
