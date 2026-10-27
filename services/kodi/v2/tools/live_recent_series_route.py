"""HP-only native acceptance for Home Recently Added TV-show routing."""

import json,os,time
from pathlib import Path
import xbmc,xbmcgui

ROOT=Path('/storage/.aster-checkpoints/aster-series-latency1')
result={'passed':False,'position':None,'show_id':None,'visible_ms':None,'players':None}
try:
    if os.uname().nodename!='AsterTV' or xbmcgui.getCurrentWindowId()!=10000:
        raise RuntimeError('recent-series-home-required')
    window=xbmcgui.Window(10000);position=None
    for index in range(10):
        xbmc.executebuiltin('SetFocus(110,'+str(index)+',absolute)');xbmc.sleep(100)
        if xbmc.getInfoLabel('Container(110).ListItem.DBTYPE')=='tvshow':
            identity=xbmc.getInfoLabel('Container(110).ListItem.DBID')
            if identity.isdecimal() and int(identity)>0:position=index;break
    if position is None:raise RuntimeError('recent-series-tvshow-unavailable')
    result.update(position=position,show_id=int(identity));started=time.monotonic()
    xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
    deadline=started+8
    while time.monotonic()<deadline and not window.getProperty('AsterSeries.PreviewWindow'):xbmc.sleep(25)
    if not window.getProperty('AsterSeries.PreviewWindow').isdecimal():raise RuntimeError('recent-series-route-timeout')
    result['visible_ms']=round((time.monotonic()-started)*1000);xbmc.sleep(750)
    xbmc.executebuiltin('Action(Back)');deadline=time.monotonic()+5
    while time.monotonic()<deadline and (window.getProperty('AsterSeries.PreviewWindow') or xbmcgui.getCurrentWindowId()!=10000):xbmc.sleep(25)
    players=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result',[])
    result['players']=players
    result['passed']=result['visible_ms']<3000 and xbmcgui.getCurrentWindowId()==10000 and not players
except Exception as error:result['code']=str(error)
ROOT.mkdir(mode=0o700,parents=True,exist_ok=True)
path=ROOT/('recent-route-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
