"""Activate, verify or roll back the second HP family reconciliation."""
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
from family_manifest_reconcile_install import CHECKPOINT2, run


if __name__ == '__main__':
    result = {}
    lock = None
    try:
        if os.uname().nodename != 'AsterTV' or len(sys.argv) != 3:
            raise ValueError('family-reconcile2-hp-arguments')
        mode, pin = sys.argv[1:]
        if mode not in ('install', 'verify', 'rollback') or not re.fullmatch('[0-9a-f]{64}', pin):
            raise ValueError('family-reconcile2-mode-pin')
        lock = os.open(str(ROOT/'deploy.lock'), os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        def idle():
            active = json.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result', [])
            return not active and xbmcgui.getCurrentWindowId() == 10000
        result = run(mode, ROOT, Path('/storage'), pin, idle=idle,
            checkpoint_path=CHECKPOINT2,
            contract_kind='hp-family-manifest-reconcile.v2')
        result.update(passed=True, home=True, timestamp_ns=time.time_ns())
    except (OSError, ValueError, KeyError, RuntimeError, BlockingIOError) as error:
        code = str(error)
        result = dict(passed=False, code=code if re.fullmatch('[a-z0-9-]{1,100}', code)
                      else type(error).__name__)
    finally:
        if lock is not None: os.close(lock)
    (ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result, indent=2))
