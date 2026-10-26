"""Single-invocation HP mixed-player endurance, avoiding harness-invoker growth."""
import hashlib,json,os
from pathlib import Path
import re,time
import xbmc,xbmcgui

ROOT=Path(__file__).resolve().parent
VIDEO=Path('/storage/.aster-private/m7-fixtures/aster-m7-test.mov')
AUDIO=Path('/storage/.aster-staging/aster-readalong3/sample.wav')
HASHES={VIDEO:'18d5578584490a6a7c2db8899040ae1af236aa4044c1e28c66243b231391568f',AUDIO:'99ae9edd408aa2fc6258d300c9d655cd4d81b88114f90fd609089a2541a5e039'}

def require(value,code):
    if not value: raise RuntimeError(code)
def rpc(method,params=None):
    value=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in value,'native-endurance-rpc'); return value.get('result')
def players(): return rpc('Player.GetActivePlayers') or []
def wait_player(kind,timeout=6):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        rows=players()
        if len(rows)==1 and rows[0].get('type')==kind:return rows[0]['playerid']
        xbmc.sleep(100)
    raise RuntimeError('native-endurance-'+kind+'-start')
def wait_idle(timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if not players():return
        xbmc.sleep(100)
    raise RuntimeError('native-endurance-stop-timeout')
def metric():
    status=Path('/proc/self/status').read_text(); rss=re.search(r'^VmRSS:\s+(\d+)\s+kB$',status,re.M)
    require(rss,'native-endurance-rss'); thermal=Path('/sys/class/thermal/thermal_zone0/temp')
    return dict(rss_kib=int(rss.group(1)),temperature_c=int(thermal.read_text())/1000 if thermal.is_file() else None,timestamp_ns=time.time_ns())

result={}; cycles=6
try:
    require(os.uname().nodename=='AsterTV' and xbmcgui.getCurrentWindowId()==10000 and not players(),'native-endurance-home-idle')
    for path,expected in HASHES.items():require(path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,'native-endurance-fixture')
    start=metric(); runs=[]
    for index in range(cycles):
        rpc('Player.Open',dict(item=dict(file=str(VIDEO)))); video=wait_player('video'); xbmc.sleep(500)
        rpc('Player.PlayPause',dict(playerid=video,play=False)); rpc('Player.PlayPause',dict(playerid=video,play=True)); wait_idle(18)
        xbmc.executebuiltin('ActivateWindow(Home)'); xbmc.sleep(2000)
        rpc('Player.Open',dict(item=dict(file=str(AUDIO)))); audio=wait_player('audio'); xbmc.sleep(500)
        rpc('Player.PlayPause',dict(playerid=audio,play=False)); rpc('Player.PlayPause',dict(playerid=audio,play=True)); rpc('Player.Stop',dict(playerid=audio)); wait_idle(4)
        xbmc.executebuiltin('ActivateWindow(Home)'); xbmc.sleep(2000); runs.append(metric())
    require(xbmcgui.getCurrentWindowId()==10000 and not players(),'native-endurance-home-return')
    result=dict(passed=True,cycles=cycles,start=start,end=metric(),runs=runs,timestamp_ns=time.time_ns())
except (OSError,RuntimeError,ValueError,KeyError) as error:
    for row in players():
        try:rpc('Player.Stop',dict(playerid=row['playerid']))
        except Exception:pass
    xbmc.executebuiltin('ActivateWindow(Home)'); code=str(error)
    result=dict(passed=False,code=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__)
(ROOT/('native-endurance-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2))
