"""Use current recovery logic with a previously pinned family candidate."""
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
import family_runtime_install as installer


if __name__ == '__main__':
    result = {}
    try:
        if os.uname().nodename != 'AsterTV' or len(sys.argv) != 5:
            raise ValueError('family-recovery-hp-arguments')
        mode, stage, pin, checkpoint = sys.argv[1:]
        if (mode != 'rollback' or not re.fullmatch('[0-9a-f]{64}', pin)
                or checkpoint not in ('aster-family-runtime1', 'aster-family-runtime2',
                                      'aster-family-runtime3', 'aster-family-runtime4')):
            raise ValueError('family-recovery-bounded-mode')
        installer.CHECKPOINT = Path('.aster-checkpoints')/checkpoint
        def idle():
            active = json.loads(xbmc.executeJSONRPC(
                '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result', [])
            return not active and xbmcgui.getCurrentWindowId() == 10000
        status = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1,
            method='Addons.GetAddonDetails', params=dict(
                addonid='script.asterruntime', properties=['enabled'])))))
        if 'error' not in status and status['result']['addon']['enabled']:
            changed = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=2,
                method='Addons.SetAddonEnabled', params=dict(
                    addonid='script.asterruntime', enabled=False)))))
            if 'error' in changed:
                raise ValueError('family-recovery-disable-failed')
        result = installer.run(mode, Path(stage), Path('/storage'), pin, idle=idle)
        xbmc.executebuiltin('UpdateLocalAddons')
        xbmc.executebuiltin('ReloadSkin')
        xbmc.sleep(1800)
        if xbmcgui.getCurrentWindowId() != 10000:
            raise ValueError('family-recovery-home-return')
        result.update(passed=True, home=True)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        result = dict(passed=False, code=str(error))
    (ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result, indent=2))
