"""ID-bound video scrub preview; no file URLs, stream resolver or auto retry."""
from __future__ import annotations
from dataclasses import dataclass,replace

class ScrubUnavailable(ValueError):pass
def require(value,message):
    if not value:raise ScrubUnavailable(message)
def milliseconds(value):
    require(isinstance(value,dict) and set(value)=={'hours','minutes','seconds','milliseconds'},'clock-unavailable')
    for key,limit in (('hours',167),('minutes',59),('seconds',59),('milliseconds',999)):
        require(type(value[key]) is int and 0<=value[key]<=limit,'clock-unavailable')
    return ((value['hours']*60+value['minutes'])*60+value['seconds'])*1000+value['milliseconds']
def clock_value(value):
    hours,value=divmod(value,3600000);minutes,value=divmod(value,60000);seconds,value=divmod(value,1000)
    return dict(hours=hours,minutes=minutes,seconds=seconds,milliseconds=value)
def clock_label(value):
    hours,value=divmod(value//1000,3600);minutes,seconds=divmod(value,60)
    return f'{hours:d}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes:d}:{seconds:02d}'

@dataclass(frozen=True)
class VideoState:
    kind:str
    identity:int
    show_id:int|None
    duration_ms:int
    elapsed_ms:int
    speed:int
    @property
    def key(self):return self.kind,self.identity,self.show_id,self.duration_ms

def read_state(rpc):
    players=rpc('Player.GetActivePlayers',{})
    require(isinstance(players,list) and len(players)==1 and players[0].get('playerid')==1
        and players[0].get('type')=='video','one-video-required')
    item=rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid'])).get('item',{})
    require(item.get('type') in ('episode','movie','musicvideo') and type(item.get('id')) is int
        and 0<item['id']<=2147483647,'indexed-video-required')
    show=item.get('tvshowid') if item['type']=='episode' else None
    if item['type']=='episode':require(type(show) is int and show>0,'episode-show-unavailable')
    props=rpc('Player.GetProperties',dict(playerid=1,properties=['time','totaltime','canseek','speed']))
    require(props.get('canseek') is True and type(props.get('speed')) is int and props['speed'] in (0,1),'seek-unavailable')
    duration=milliseconds(props.get('totaltime'));elapsed=milliseconds(props.get('time'))
    require(1000<=duration<=604799999 and 0<=elapsed<duration,'duration-unavailable')
    return VideoState(item['type'],item['id'],show,duration,elapsed,props['speed'])

@dataclass(frozen=True)
class VideoPreview:
    state:VideoState
    target_ms:int
    def __post_init__(self):
        require(isinstance(self.state,VideoState) and type(self.state.duration_ms) is int
            and 1000<=self.state.duration_ms<=604799999 and type(self.target_ms) is int
            and 0<=self.target_ms<=self.state.duration_ms-1000,'invalid-preview')
    @classmethod
    def start(cls,state):return cls(state,min(state.elapsed_ms,state.duration_ms-1000))
    def adjust(self,direction):
        require(type(direction) is int and direction in (-1,1),'invalid-direction')
        return replace(self,target_ms=max(0,min(self.state.duration_ms-1000,self.target_ms+direction*5000)))
    @property
    def percentage(self):return self.target_ms/self.state.duration_ms*100

class ScrubSession:
    def __init__(self,rpc,epoch=lambda:0):
        self.rpc=rpc;self.epoch=epoch;self.initial_epoch=epoch()
        self.preview=VideoPreview.start(read_state(rpc));self.phase='preview';self.error=None
        require(epoch()==self.initial_epoch,'video-changed')
    def adjust(self,direction):
        require(self.phase=='preview','preview-closed');self.preview=self.preview.adjust(direction)
    def cancel(self):
        if self.phase=='preview':self.phase='cancelled'
    def apply(self):
        require(self.phase=='preview','seek-already-consumed')
        # Claim the single apply before any synchronous native read/callback.
        self.phase='checking'
        try:
            require(self.epoch()==self.initial_epoch,'video-changed')
            current=read_state(self.rpc);require(current.key==self.preview.state.key,'video-changed')
            check=read_state(self.rpc);require(check.key==current.key,'video-changed')
            require(self.epoch()==self.initial_epoch,'video-changed')
            self.phase='seeking'
            self.rpc('Player.Seek',dict(playerid=1,value=dict(time=clock_value(self.preview.target_ms))))
            self.phase='applied'
            after=read_state(self.rpc)
            require(self.epoch()==self.initial_epoch and after.key==current.key,'video-changed')
            if after.key==current.key and check.speed==0 and after.speed==1:
                self.rpc('Player.PlayPause',dict(playerid=1,play=False))
        except Exception:
            unknown=self.phase in ('seeking','applied')
            self.phase='uncertain' if unknown else 'rejected';self.error='seek-outcome-unknown' if unknown else 'video-changed-or-unavailable'
            raise ScrubUnavailable(self.error) from None
