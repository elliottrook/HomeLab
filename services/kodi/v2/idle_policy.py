"""Pure privacy-first idle decisions. No Kodi, playback, settings or I/O effects."""
from __future__ import annotations
from dataclasses import dataclass
import math

MODES=frozenset(('aster','dim','black','disabled'))
WAKE_INPUTS=frozenset(('navigation','select','back','home'))

@dataclass(frozen=True)
class Config:
    mode:str='black'
    minutes:int=3
    def __post_init__(self):
        if type(self.mode) is not str or self.mode not in MODES or type(self.minutes) is not int or not 1<=self.minutes<=60:
            raise ValueError('invalid-idle-config')

@dataclass(frozen=True)
class Observation:
    idle_seconds:float|None
    media_active:bool|None
    alarm_active:bool|None
    busy:bool|None
    sensitive_surface:bool|None

@dataclass(frozen=True)
class Decision:
    enter:bool
    effect:str
    reason:str

def decide(config:Config,observed:Observation,*,aster_supported=False):
    if config.mode=='disabled':return Decision(False,'none','Disabled')
    seconds=observed.idle_seconds
    if (type(seconds) not in (float,int) or not math.isfinite(seconds) or seconds<0 or
        any(type(v) is not bool for v in (observed.media_active,observed.alarm_active,
            observed.busy,observed.sensitive_surface))):
        return Decision(False,'none','State not verified')
    if observed.media_active:return Decision(False,'none','Media owns the foreground')
    if observed.alarm_active:return Decision(False,'none','Alarm requires attention')
    if observed.busy:return Decision(False,'none','Interaction in progress')
    if seconds<config.minutes*60:return Decision(False,'none','Not idle long enough')
    if observed.sensitive_surface:return Decision(True,'black','Private surface hidden')
    if config.mode=='aster' and aster_supported is not True:
        return Decision(True,'black','Aster presentation unavailable; Black fallback')
    return Decision(True,config.mode,'Idle')

@dataclass(frozen=True)
class Context:
    window:int
    focus:int
    def __post_init__(self):
        if (type(self.window) is not int or not 1<=self.window<=99999 or
            type(self.focus) is not int or not 1<=self.focus<=999999):
            raise ValueError('invalid-idle-context')

@dataclass(frozen=True)
class Wake:
    consume:bool
    close_owned:bool
    restore_focus:int|None

class Session:
    """Caller owns the overlay. Never replays input or changes media/settings."""
    def __init__(self,source:Context):self.source=source;self.closed=False
    def wake(self,kind,underlying:Context,*,owned_visible,foreign_media):
        if self.closed or kind not in WAKE_INPUTS or owned_visible is not True:
            return Wake(False,False,None)
        self.closed=True
        restore=self.source.focus if foreign_media is False and underlying==self.source else None
        return Wake(True,True,restore)
