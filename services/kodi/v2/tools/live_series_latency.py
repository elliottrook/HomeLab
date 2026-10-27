"""HP-only read-only timing probe for the current series page."""

import json,os,time
from pathlib import Path
import xbmc,xbmcgui

ROOT=Path('/storage/.aster-checkpoints/aster-series-latency1')
result={'passed':False,'show_id':None,'visible_ms':None,'returned_home':False,'players':None}
try:
    if os.uname().nodename!='AsterTV' or len(__import__('sys').argv)!=2 or not __import__('sys').argv[1].isdecimal():
        raise RuntimeError('series-latency-probe-boundary')
    show_id=int(__import__('sys').argv[1]);result['show_id']=show_id
    home=xbmcgui.Window(10000)
    if xbmcgui.getCurrentWindowId()!=10000 or home.getProperty('AsterSeries.PreviewWindow'):
        raise RuntimeError('series-latency-probe-home')
    started=time.monotonic()
    xbmc.executebuiltin('RunScript(script.asterruntime,aster-series-preview24,default,'+str(show_id)+')')
    deadline=started+8
    while time.monotonic()<deadline and not home.getProperty('AsterSeries.PreviewWindow'):xbmc.sleep(25)
    identity=home.getProperty('AsterSeries.PreviewWindow')
    if not identity.isdecimal():raise RuntimeError('series-latency-probe-timeout')
    result['visible_ms']=round((time.monotonic()-started)*1000)
    xbmc.sleep(1500);xbmc.executebuiltin('TakeScreenshot('+str(ROOT/'latency-visible.png')+',false)');xbmc.sleep(500)
    xbmc.executebuiltin('Action(Back)')
    deadline=time.monotonic()+5
    while time.monotonic()<deadline and (home.getProperty('AsterSeries.PreviewWindow') or xbmcgui.getCurrentWindowId()!=10000):xbmc.sleep(25)
    players=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result',[])
    result['players']=players;result['returned_home']=xbmcgui.getCurrentWindowId()==10000
    result['passed']=result['visible_ms']<3000 and result['returned_home'] and not players
except Exception as error:
    result['code']=str(error)
ROOT.mkdir(mode=0o700,parents=True,exist_ok=True)
path=ROOT/('latency-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
