"""Normal HP Books sleep selector; no direct Stop, progress or server writes."""
import json,os,uuid
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
home=xbmcgui.Window(10000);token=home.getProperty('AsterBooks.SleepToken')
if token and xbmcgui.getCurrentWindowId()==10502 and xbmc.getCondVisibility('Player.HasAudio'):
    selected=xbmcgui.Dialog().select('Sleep timer',['Off','15 minutes','30 minutes','45 minutes','60 minutes'])
    if 0<=selected<=4 and home.getProperty('AsterBooks.SleepToken')==token:
        home.setProperty('AsterBooks.SleepRequest',json.dumps(dict(token=token,request=uuid.uuid4().hex,minutes=(0,15,30,45,60)[selected])))
