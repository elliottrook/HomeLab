"""Content-free Aster logo drift; no title, clock or household inputs."""
from dataclasses import dataclass
import math

POSITIONS=((100,90),(800,90),(1500,90),(1500,423),(1500,755),
    (800,755),(100,755),(100,423),(800,423))
MARK_WIDTH=320
MARK_HEIGHT=208
PERIOD=30

@dataclass(frozen=True)
class Frame:
    visible:bool=False
    x:int=120
    y:int=110

def frame(mode,elapsed):
    if mode!='aster' or type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0:
        return Frame()
    index=int(elapsed//PERIOD)%len(POSITIONS)
    following=(index+1)%len(POSITIONS)
    phase=(elapsed%PERIOD)/PERIOD
    # A cosine ease keeps the movement calm at each turn without ever leaving
    # the screen blank. The mark remains in motion to protect the display.
    eased=(1-math.cos(math.pi*phase))/2
    x=round(POSITIONS[index][0]+(POSITIONS[following][0]-POSITIONS[index][0])*eased)
    y=round(POSITIONS[index][1]+(POSITIONS[following][1]-POSITIONS[index][1])*eased)
    return Frame(True,x,y)
