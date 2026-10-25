"""Read-only HP screen enum/mode projection, without exporting GUI settings."""
import json,os,time
from pathlib import Path
import xbmc
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
def read(method,params):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    if 'error' in reply:raise RuntimeError('display-read-failed')
    return reply['result']
labels=read('XBMC.GetInfoLabels',dict(labels=['System.ScreenResolution','System.ScreenWidth','System.ScreenHeight','System.FPS']))
settings=read('Settings.GetSettings',dict(level='expert',filter=dict(section='system',category='display')))
selected=[{k:r[k] for k in ('id','value','options') if k in r} for r in settings['settings']
    if r['id'] in ('videoscreen.resolution','videoscreen.screenmode','videoscreen.screen','videoscreen.monitor')]
path=Path('/storage/.aster-checkpoints/aster-global-search-20261024')/('display-projection-'+str(time.time_ns())+'.json')
path.write_text(json.dumps(dict(labels=labels,settings=selected),indent=2));path.chmod(0o600)
