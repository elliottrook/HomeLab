"""Ephemeral owned-listening sleep timer; no persistence, Kodi imports or API."""
from __future__ import annotations
from dataclasses import dataclass
import math,time
from books_progress import Scope,require

PRESETS=(15,30,45,60)
def owned_audio_player(players):
    """Kodi 21 adds playertype; compare identity, not the entire RPC dict."""
    return (isinstance(players,list) and len(players)==1 and isinstance(players[0],dict)
            and type(players[0].get('playerid')) is int and players[0]['playerid']==0
            and players[0].get('type')=='audio'
            and players[0].get('playertype','internal')=='internal')

def countdown_label(remaining):
    """Wall-clock seconds for the final two minutes; rounded minutes before."""
    remaining=max(0,int(remaining))
    return ('Sleep in '+f'{remaining//60}:{remaining%60:02d}' if remaining<=120
            else 'Sleep in '+str((remaining+59)//60)+' min')

@dataclass(frozen=True)
class Listening:
    scope:Scope
    url:str

class SleepTimer:
    def __init__(self,current,save,stop,report,*,clock=time.monotonic):
        self.current=current;self.save=save;self.stop=stop;self.report=report;self.clock=clock
        self.scope=None;self.deadline=None;self.state='off'
    def cancel(self,reason='Sleep timer off'):
        self.scope=None;self.deadline=None;self.state='off';self.report(self.state,reason)
    def arm(self,minutes):
        require(type(minutes) is int and minutes in PRESETS,'sleep-preset-required')
        context=self.current()
        require(isinstance(context,Listening) and isinstance(context.scope,Scope)
            and isinstance(context.url,str) and bool(context.url),'owned-listening-required')
        self.scope=context.scope;self.deadline=self.clock()+minutes*60;self.state='armed'
        self.report('armed','Sleep in '+str(minutes)+' min')
    def remaining(self):
        return max(0,math.ceil(self.deadline-self.clock())) if self.deadline is not None else None
    def tick(self,*,known=True):
        if self.deadline is None or not known:return
        context=self.current()
        if context is None or context.scope!=self.scope:
            self.cancel('Sleep cancelled · playback changed');return
        if self.clock()<self.deadline:return
        # Consume before any I/O: unknown Stop results are never replayed.
        scope=self.scope;self.scope=None;self.deadline=None;self.state='expiring'
        saved=True
        try:saved=self.save(context.url) is True
        except Exception:saved=False
        latest=self.current()
        if latest is None or latest.scope!=scope or latest.url!=context.url:
            self.cancel('Sleep cancelled · playback changed');return
        try:
            require(self.stop(context.url) is True,'sleep-stop-unacknowledged')
            self.state='stopped';self.report('stopped','Sleep timer ended' if saved else 'Sleep ended · position not saved')
        except Exception:
            self.state='uncertain';self.report('uncertain','Sleep stop unverified · no automatic retry')
