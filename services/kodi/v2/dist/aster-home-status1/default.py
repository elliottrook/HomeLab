"""Normal Home's local-only schema4 display adapter; no network or HA actions."""
from pathlib import Path
import sys
import xbmc
import xbmcgui
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,'/storage/.kodi/addons/skin.asterhome/tools')
from home_status_model import view
import hub_data

FEED=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home-dashboard.json')
SCRIPT='/storage/.aster-staging/aster-home-status1/default.py'

def main(action):
    if action=='leave':
        xbmc.executebuiltin('CancelAlarm(AsterHomeStatus,silent)')
        hub_data.main('home','home_stop')
        return
    if xbmcgui.getCurrentWindowId()!=11112:return
    window=xbmcgui.Window(11112)
    if action=='entry':
        hub_data.main('home')
        window.setProperty('AsterHub.HomeSection','Household')
        window.setProperty('AsterHub.HomeFilter','overview')
        xbmc.executebuiltin('AlarmClock(AsterHomeStatus,RunScript('+SCRIPT+',tick),00:30,silent,loop)')
    elif action not in ('refresh','tick','overview','lighting'):return
    if action in ('overview','lighting'):window.setProperty('AsterHub.HomeFilter',action)
    section=window.getProperty('AsterHub.HomeFilter') or 'overview'
    try:
        if FEED.is_symlink() or FEED.stat().st_nlink!=1:raise ValueError('home-status-file-type')
        with FEED.open('rb') as stream:raw=stream.read(262145)
    except (OSError,ValueError):raw=b''
    result=view(raw,section=section)
    if xbmcgui.getCurrentWindowId()!=11112:return
    # Repeated local checks preserve selection, timer and camera properties.
    for key,value in result.properties.items():window.setProperty('AsterHub.Home'+key,value)
    window.setProperty('AsterHub.HomeSection','Lighting' if section=='lighting' else 'Household')
    window.setProperty('AsterHub.HomeSourceNotice',result.notice)
    window.setProperty('AsterHub.HomeSourceState',result.state)
    listing=window.getControl(500)
    previous=listing.getSelectedPosition()
    listing.reset();listing.addItems([xbmcgui.ListItem(title,detail) for title,detail in result.rows])
    if action not in ('lighting','overview') and previous>=0:listing.selectItem(min(previous,len(result.rows)-1))
    if action in ('lighting','overview'):xbmc.executebuiltin('Control.SetFocus(500)')

if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'refresh')
