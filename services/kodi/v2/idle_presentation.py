"""Content-free Aster logo constellation; no title or household inputs."""
from dataclasses import dataclass
import math

MARK_WIDTH=320
MARK_HEIGHT=206
PERIOD=14
VISIBLE_FROM=1
VISIBLE_UNTIL=10.5

@dataclass(frozen=True)
class Frame:
    visible:bool=False
    x:int=120
    y:int=110

def frame(mode,elapsed):
    if mode!='aster' or type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0:
        return Frame()
    cycle=int(elapsed//PERIOD)
    def mix(value):
        value=(value+0x9e3779b9)&0xffffffff
        value=((value^(value>>16))*0x85ebca6b)&0xffffffff
        value=((value^(value>>13))*0xc2b2ae35)&0xffffffff
        return value^(value>>16)
    x=84+mix(cycle*2)%(1920-168-MARK_WIDTH+1)
    y=84+mix(cycle*2+1)%(1080-168-MARK_HEIGHT+1)
    phase=elapsed%PERIOD
    return Frame(VISIBLE_FROM<=phase<VISIBLE_UNTIL,x,y)
