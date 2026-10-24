"""Close only the foreground idle HP series preview before a staged revision."""
import json,os,time
import xbmc,xbmcgui

def require(value,message):
    if not value:raise RuntimeError(message)
require(os.uname().nodename=='AsterTV','hp-only')
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Input.ExecuteAction'},'close-preview-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-action-unavailable');return reply['result']
require(not rpc('Player.GetActivePlayers'),'idle-required')
identity=xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)')
if identity:
    require(identity.isdecimal() and xbmcgui.getCurrentWindowId()==int(identity)
        and xbmcgui.getCurrentWindowDialogId() in (0,9999),'foreground-preview-only')
    rpc('Input.ExecuteAction',dict(action='back'))
    deadline=time.monotonic()+5
    while xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)') and time.monotonic()<deadline:xbmc.sleep(80)
    require(not xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)'),'preview-not-closed')
