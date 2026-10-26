"""Kodi-native adoption and recovery wrapper for the consolidated HP family."""
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from family_recovery_install import inspect,run


def require(value,code):
    if not value: raise RuntimeError(code)


if __name__=='__main__':
    result={}
    try:
        require(os.uname().nodename=='AsterTV' and len(sys.argv)==3,'family7-hp-arguments')
        mode,pin=sys.argv[1:]; require(re.fullmatch('[0-9a-f]{64}',pin),'family7-pin-format')
        inspect(ROOT,pin)
        lock=os.open(str(ROOT/'deploy.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            def rpc(method,params=None):
                reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(
                    jsonrpc='2.0',id=1,method=method,params=params or {}))))
                require('error' not in reply,'family7-rpc'); return reply.get('result')
            def idle(): return not (rpc('Player.GetActivePlayers') or []) and xbmcgui.getCurrentWindowId()==10000
            result=run(mode,ROOT,Path('/storage'),pin,idle=idle)
            if mode in ('rollback','install'):
                xbmc.executebuiltin('UpdateLocalAddons'); xbmc.executebuiltin('ReloadSkin'); xbmc.sleep(1800)
            require(xbmcgui.getCurrentWindowId()==10000,'family7-home-return')
            result.update(passed=True,home=True,timestamp_ns=time.time_ns())
        finally:
            os.close(lock)
    except (OSError,ValueError,RuntimeError,KeyError) as error:
        code=str(error); result=dict(passed=False,code=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__)
    (ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2))
