"""Read-only HP renderer/idle diagnostics and private native capture."""
import json
import os
from pathlib import Path
import time
import xbmc
import xbmcgui
if os.uname().nodename != 'AsterTV': raise RuntimeError('hp-only')
cp=Path('/storage/.aster-checkpoints')/('aster-reading-render-'+str(time.time_ns()))
cp.mkdir(mode=0o700)
conditions=('System.ScreenSaverActive','System.DPMSActive','Window.IsVisible(screensaver)',
            'Window.IsActive(screensaver)','System.IdleTime(180)')
data=dict(window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),
          conditions={k:xbmc.getCondVisibility(k) for k in conditions})
(cp/'state.json').write_text(json.dumps(data));(cp/'state.json').chmod(0o600)
xbmc.executebuiltin('TakeScreenshot('+str(cp/'screen.png')+')');xbmc.sleep(700)
