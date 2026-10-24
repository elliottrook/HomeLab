"""Shared HP native remote check; called only by approved owned-player tests."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import os
import subprocess
from pathlib import Path
import xbmc


def check(rpc,label,focus,until,press,select):
    _require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
    def state():return rpc('Player.GetProperties',dict(playerid=0,properties=['position','speed','time','totaltime']))
    def elapsed(props):
        t=props['time'];return ((t['hours']*60+t['minutes'])*60+t['seconds'])*1000+t['milliseconds']
    before=state();item=rpc('Player.GetItem',dict(playerid=0,properties=[]))['item']
    _require((before['speed']==0 and focus(400)), ('paused Play origin required'))
    press('up');until(lambda:focus(611),'album scrub focus')
    press('right');press('right')
    _require(('OK apply' in label('Window.Property(Album.ControlHint)')), ('native-check-failed'))
    _require((abs(elapsed(state())-elapsed(before))<1500), ('preview must not seek'))
    press('back');until(lambda:focus(400),'scrub cancel restores Play')
    _require((state()['speed']==0 and abs(elapsed(state())-elapsed(before))<1500), ('native-check-failed'))
    press('up');until(lambda:focus(611),'second scrub focus')
    press('right');press('right');select()
    until(lambda:focus(400) and state()['speed']==0 and abs(elapsed(state())-elapsed(before)-10000)<2000,'one paused scrub applied')
    until(lambda:label('Window.Property(Album.ControlHint)')=='Resume','seek worker released transport')
    after=state()
    _require((after['position']==before['position']), ('native-check-failed'))
    _require((rpc('Player.GetItem',dict(playerid=0,properties=[]))['item']==item), ('native-check-failed'))
    screenshot=Path('/storage/.aster-staging/album-scrub-details.png')
    subprocess.run(['kodi-send','--action=TakeScreenshot('+str(screenshot)+')'],check=True,stdout=subprocess.DEVNULL)
    until(lambda:screenshot.is_file(),'scrub screenshot saved')
    return True
