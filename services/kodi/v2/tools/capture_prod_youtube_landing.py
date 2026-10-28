"""Capture the production Aster YouTube landing after its bounded focus delay."""
import json
from pathlib import Path
import time
import xbmc
import xbmcgui

output = Path('/tmp/astertv-prod-youtube-landing.png')
record = Path('/tmp/astertv-prod-youtube-landing.json')
result = {'captured': False}
try:
    if xbmcgui.getCurrentWindowId() != 10000:
        raise RuntimeError('home-required')
    xbmc.executebuiltin('Control.SetFocus(136)')
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not xbmc.getCondVisibility('Control.HasFocus(136)'):
        xbmc.sleep(100)
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.ExecuteAction","params":{"action":"select"}}')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if (xbmcgui.getCurrentWindowId() == 10025
                and xbmc.getInfoLabel('Container.FolderPath') == 'plugin://plugin.video.youtube/'
                and xbmc.getCondVisibility('Control.HasFocus(9530)')):
            break
        xbmc.sleep(100)
    else:
        raise RuntimeError('landing-not-ready')
    xbmc.sleep(500)
    if output.exists(): output.unlink()
    xbmc.executebuiltin('TakeScreenshot(%s,false)' % output)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not output.exists(): xbmc.sleep(100)
    if not output.exists(): raise RuntimeError('screenshot-missing')
    result = {'captured': True, 'bytes': output.stat().st_size}
except Exception as error:
    result['error'] = str(error)
finally:
    xbmc.executebuiltin('ActivateWindow(Home)')
    record.write_text(json.dumps(result, indent=2))
