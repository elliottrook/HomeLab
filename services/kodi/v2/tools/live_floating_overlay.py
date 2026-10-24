"""HP native four-page icon layout/focus smoke, synthetic video OSD test.

No real video playback/history or settings changes. Other page checks are idle.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import json, os, sys, time
from pathlib import Path
import xbmc, xbmcgui
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))


def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    _require(('error' not in result), ('native-rpc-failed'))
    return result['result']
def label(key):return rpc('XBMC.GetInfoLabels',dict(labels=[key]))[key]
def focused(i):return rpc('XBMC.GetInfoBooleans',dict(booleans=[f'Control.HasFocus({i})']))[f'Control.HasFocus({i})']
def until(check,message,timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if check():return
        xbmc.sleep(50)
    raise AssertionError(message)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def screenshot(name):
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/floating-'+name+'.png)')
    xbmc.sleep(400)


_require((not rpc('Player.GetActivePlayers')), ('native-check-failed'))
_require((rpc('Playlist.GetItems',dict(playlistid=0))['limits']['total']==0), ('native-check-failed'))
checks=[];passed=False
try:
    for window,identity,name in ((1121,9100,'album'),(10502,9000,'books'),(1111,305,'digest')):
        xbmc.executebuiltin('ActivateWindow('+str(window)+')')
        until(lambda:xbmcgui.getCurrentWindowId()==(10000+window if window<10000 else window),'open '+name)
        xbmc.executebuiltin('SetFocus('+str(identity)+')')
        until(lambda:focused(identity),'focused '+name)
        _require((label('Control.GetLabel('+str(identity)+')')), ('native-check-failed'))
        screenshot(name)
        checks.append(name+' native page, labelled control and focus')
        xbmc.executebuiltin('ActivateWindow(Home)')
        until(lambda:xbmcgui.getCurrentWindowId()==10000,'return Home')
        xbmc.sleep(350)
    fixture='/storage/.aster-staging/aster-osd-fixture.avi'
    _require((Path(fixture).is_file()), ('native-check-failed'))
    rpc('Player.Open',dict(item=dict(file=fixture)))
    until(lambda:any(p['type']=='video' for p in rpc('Player.GetActivePlayers')),'synthetic video playing')
    xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
    until(lambda:xbmcgui.getCurrentWindowId()==12005,'full-screen synthetic video')
    xbmc.sleep(750)
    xbmc.executebuiltin('ActivateWindow(VideoOSD)')
    until(lambda:focused(602),'video Pause focus')
    screenshot('video')
    select()
    until(lambda:rpc('Player.GetProperties',dict(playerid=1,properties=['speed']))['speed']==0,'video paused')
    # Kodi may retain the hidden Pause control's ID while Play occupies its
    # slot. Test the second physical Select, rather than assuming a focus ID.
    paused_focus=rpc('GUI.GetProperties',dict(properties=['currentcontrol']))
    checks.append('paused focus '+str(paused_focus.get('currentcontrol',{}).get('id')))
    select()
    until(lambda:rpc('Player.GetProperties',dict(playerid=1,properties=['speed']))['speed']==1,'video resumed')
    # Reach all ten video slots through the existing remote navigation graph.
    xbmc.executebuiltin('SetFocus(600)');until(lambda:focused(600),'Previous')
    for identity in (601,602,606,607,603,70043,7100,7101,7102):
        press('right');until(lambda:focused(identity),'video control '+str(identity))
    screenshot('video-quality')
    select()
    until(lambda:rpc('XBMC.GetInfoBooleans',dict(booleans=['Window.IsVisible(osdvideosettings)']))['Window.IsVisible(osdvideosettings)'],'Quality opens native settings')
    press('back');xbmc.sleep(400)
    checks.append('synthetic video Pause/Resume, all ten icon slots and Quality settings')
    passed=True
finally:
    players=rpc('Player.GetActivePlayers')
    if players:
        _require((len(players)==1 and players[0]['type']=='video'), ('unexpected-player-preserve'))
        item=rpc('Player.GetItem',dict(playerid=1,properties=['file']))['item']
        _require((item.get('file')=='/storage/.aster-staging/aster-osd-fixture.avi'), ('unrelated-media-preserve'))
        rpc('Player.Stop',dict(playerid=1))
    xbmc.executebuiltin('ActivateWindow(Home)')
    until(lambda:not rpc('Player.GetActivePlayers'),'idle after fixture')
    root=Path('/storage/.aster-checkpoints/aster-floating-controls-20261024')
    p=root/('native-'+str(time.time_ns())+'.json')
    p.write_text(json.dumps(dict(passed=passed,checks=checks,synthetic_video=True,no_real_video_history=True,
        checks_enforced=True,python_optimization=sys.flags.optimize)))
    p.chmod(0o600)
