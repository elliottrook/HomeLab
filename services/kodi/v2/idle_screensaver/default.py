"""HP-only native saver. Never dispatches a wake key or changes playback/settings."""
import json
import os
from pathlib import Path
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from idle_presentation import frame
IDENTITY='screensaver.asterhome.v2lab'

def active():return xbmc.getCondVisibility('System.ScreenSaverActive')
def attention():
    return xbmc.getCondVisibility('Player.HasMedia') or any(
        xbmc.getInfoLabel('Window(11112).Property(AsterHub.'+name+')')=='true'
        for name in ('HomeTimerActive','HomeTimerExpired'))
def wake_noop():
    # Native SendAction wakes the saver; NoOp cannot activate a page or media.
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.ExecuteAction","params":{"action":"noop"}}'))
    return 'error' not in reply

def main():
    if os.uname().nodename!='AsterTV' or not active():return
    addon=xbmcaddon.Addon()
    if addon.getAddonInfo('id')!=IDENTITY:return
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Settings.GetSettingValue","params":{"setting":"screensaver.mode"}}'))
    if reply.get('result',{}).get('value')!=IDENTITY:return
    if attention() or xbmcgui.getCurrentWindowDialogId() not in (-1,0,9999):
        wake_noop();return
    mode=addon.getSettingString('presentation')
    if mode not in ('black','aster'):mode='black'

    class Lifecycle(xbmc.Monitor):
        def onScreensaverDeactivated(self):self.finished=True
    class Saver(xbmcgui.WindowXMLDialog):
        def onInit(self):
            self.ready=True;self.getControl(10).setVisible(False)
            xbmcgui.Window(10000).setProperty('AsterIdle.Window',str(xbmcgui.getCurrentWindowDialogId()))
        def onAction(self,action):self.user_activity=True

    lifecycle=Lifecycle();lifecycle.finished=False
    window=Saver('AsterIdle.xml',str(ROOT),'Default','1080i')
    window.ready=False;window.user_activity=False;window.show()
    start=time.monotonic();previous=None
    try:
        while not lifecycle.finished and active() and not lifecycle.waitForAbort(.1):
            if attention() or window.user_activity:
                wake_noop();break
            current=frame(mode,time.monotonic()-start)
            if window.ready and current!=previous:
                image=window.getControl(10)
                image.setVisible(False);image.setPosition(current.x,current.y)
                image.setVisible(current.visible);previous=current
    finally:
        window.close();xbmcgui.Window(10000).clearProperty('AsterIdle.Window')
        del window

if __name__=='__main__':main()
