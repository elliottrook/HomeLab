"""Activate or roll back the HP-only self-contained Aster runtime."""
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

import xbmc
import xbmcgui

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from family_runtime_install import inspect, run


def require(value, code):
    if not value:
        raise AssertionError(code)


if __name__ == '__main__':
    require(os.uname().nodename == 'AsterTV' and len(sys.argv) == 3,
            'family-runtime-hp-arguments')
    mode, pin = sys.argv[1:]
    require(re.fullmatch('[0-9a-f]{64}', pin), 'family-runtime-pin-format')
    inspect(ROOT, Path('/storage'), pin)
    lock = os.open(str(ROOT/'deploy.lock'), os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        def rpc(method, params=None):
            require(method in ('Addons.GetAddonDetails', 'Addons.SetAddonEnabled'),
                    'family-runtime-addon-rpc')
            reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(
                jsonrpc='2.0', id=1, method=method, params=params or {}))))
            require('error' not in reply, 'family-runtime-addon-rpc')
            return reply['result']
        def enabled():
            return rpc('Addons.GetAddonDetails', dict(
                addonid='script.asterruntime', properties=['enabled']))['addon']['enabled']
        def idle():
            active = json.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result', [])
            return not active and xbmcgui.getCurrentWindowId() == 10000
        if mode == 'rollback':
            require(enabled(), 'family-runtime-addon-not-enabled')
            rpc('Addons.SetAddonEnabled', dict(
                addonid='script.asterruntime', enabled=False))
            require(not enabled(), 'family-runtime-addon-disable-failed')
        result = run(mode, ROOT, Path('/storage'), pin, idle=idle)
        if mode in ('install', 'rollback'):
            xbmc.executebuiltin('UpdateLocalAddons')
            if mode == 'install':
                for _ in range(20):
                    xbmc.sleep(250)
                    try:
                        active = enabled()
                        break
                    except AssertionError:
                        continue
                else:
                    raise AssertionError('family-runtime-addon-not-discovered')
                if not active:
                    rpc('Addons.SetAddonEnabled', dict(
                        addonid='script.asterruntime', enabled=True))
                require(enabled(), 'family-runtime-addon-enable-failed')
            xbmc.executebuiltin('ReloadSkin')
            xbmc.sleep(1800)
        if mode == 'verify':
            require(enabled(), 'family-runtime-addon-not-enabled')
        require(xbmcgui.getCurrentWindowId() == 10000, 'family-runtime-home-return')
        result.update(passed=True, home=True, timestamp_ns=time.time_ns())
    except (OSError, AssertionError, ValueError, KeyError, RuntimeError) as error:
        code = str(error)
        result = dict(passed=False, code=code if re.fullmatch('[a-z0-9-]{1,100}', code)
                      else type(error).__name__)
    finally:
        os.close(lock)
    (ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result, indent=2))
