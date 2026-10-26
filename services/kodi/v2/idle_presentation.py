"""Content-free, low-work idle frames; no title, clock or household inputs."""
from dataclasses import dataclass
import math

POSITIONS=((120,110),(880,110),(1640,110),(1640,460),(1640,810),
    (880,810),(120,810),(120,460),(880,460))
MARK_SIZE=160
PERIOD=45

@dataclass(frozen=True)
class Frame:
    visible:bool=False
    x:int=120
    y:int=110

def frame(mode,elapsed):
    if mode!='aster' or type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0:
        return Frame()
    index=int(elapsed//PERIOD)%len(POSITIONS)
    x,y=POSITIONS[index]
    return Frame(2<=elapsed%PERIOD<PERIOD-2,x,y)
