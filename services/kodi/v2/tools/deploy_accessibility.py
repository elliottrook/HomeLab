"""HP/Home-idle accessibility overlay activation and rollback."""
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
from accessibility_install import inspect, run


def require(value, code):
    if not value:
        raise AssertionError(code)


if __name__ == '__main__':
    require(os.uname().nodename == 'AsterTV' and len(sys.argv) == 3,
            'accessibility-hp-arguments')
    mode, pin = sys.argv[1:]
    require(re.fullmatch('[0-9a-f]{64}', pin), 'accessibility-pin-format')
    inspect(ROOT, Path('/storage'), pin)
    lock = os.open(str(ROOT/'deploy.lock'), os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        def idle():
            active = json.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"')).get('result', [])
            return not active and xbmcgui.getCurrentWindowId() == 10000
        result = run(mode, ROOT, Path('/storage'), pin, idle=idle)
        if mode in ('install', 'rollback'):
            xbmc.executebuiltin('ReloadSkin')
            xbmc.sleep(1800)
        require(xbmcgui.getCurrentWindowId() == 10000, 'accessibility-home-return')
        result.update(passed=True, home=True, timestamp_ns=time.time_ns())
    except (OSError, AssertionError, ValueError, KeyError, RuntimeError) as error:
        code = str(error)
        result = dict(passed=False, code=code if re.fullmatch('[a-z0-9-]{1,100}', code)
                      else type(error).__name__)
    finally:
        os.close(lock)
    (ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result, indent=2))
