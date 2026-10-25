"""Close only this lab fixture's owned series player through normal Back."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
def rpc(method,params=None):
    if method not in ('Player.GetActivePlayers','Player.GetItem'):raise RuntimeError('read-only')
    return json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))['result']
fixture=json.loads(Path('/storage/.aster-checkpoints/aster-series-playback-20261024/fixture.json').read_text())['fixture']
home=xbmcgui.Window(10000)
for _ in range(5):
    if rpc('Player.GetActivePlayers'):
        item=rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid']))['item']
        if item.get('tvshowid')!=fixture['show_id'] or not home.getProperty('AsterSeries.PreviewWindow'):raise RuntimeError('foreign-player-no-cleanup')
    elif not home.getProperty('AsterSeries.PreviewWindow'):break
    xbmc.executebuiltin('Action(Back)');xbmc.sleep(1200)
if rpc('Player.GetActivePlayers') or home.getProperty('AsterSeries.PreviewWindow'):raise RuntimeError('cleanup-incomplete')
xbmc.executebuiltin('ActivateWindow(Home)')
