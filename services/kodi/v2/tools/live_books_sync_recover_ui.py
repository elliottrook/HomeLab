"""Bounded recovery of the native test's still-selected Books stream through UI."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(v,c):
    if not v:raise RuntimeError(c)
require(os.uname().nodename=='AsterTV' and xbmcgui.getCurrentWindowId()==10502,'hp-books-ui-required')
folder=xbmc.getInfoLabel('Container.FolderPath');selected=xbmc.getInfoLabel('Container(50).ListItem.FileNameAndPath')
require(folder.startswith('plugin://plugin.audio.asterbooks/') and selected.startswith('http://127.0.0.1:'),'normal-books-source-required')
player=xbmc.Player()
if player.isPlaying():require(player.isPlayingAudio() and player.getPlayingFile()==selected,'selected-owned-audio-required')
def select(identity):
    xbmc.executebuiltin('SetFocus('+str(identity)+')');xbmc.sleep(200)
    require(xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'),'visible-control-required')
    xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def until(check,code):
    end=time.monotonic()+10
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(100)
    raise RuntimeError(code)
if player.isPlaying():select(9104);until(lambda:not player.isPlaying(),'stop-not-confirmed')
select(9000);until(lambda:xbmcgui.getCurrentWindowId()!=10502,'books-exit-not-confirmed')
xbmc.sleep(800)
result=dict(ui_stop_verified=not player.isPlaying(),window=xbmcgui.getCurrentWindowId())
path=Path('/storage/.aster-checkpoints/aster-books-sync-20261025')/('ui-recovery-'+str(time.time_ns())+'.json')
path.write_text(json.dumps(result));path.chmod(0o600)
