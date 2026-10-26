"""HP native compact Diagnostics menu and Network return-context proof."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
ROOT=Path('/storage/.aster-staging/aster-network-preview5')
PIN='04fe8bf7d4ac047957ebf89f84be42cb195ccae41a63fde88a820f659cb987d6'
TARGET=Path('/storage/.kodi/addons/skin.asterhome/1080i/Settings.xml')

def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(code)
def homeprop(key):return xbmcgui.Window(10000).getProperty('AsterNetwork.'+key)
def focus(n):return xbmc.getCondVisibility('Control.HasFocus('+str(n)+')')
def press(action):
    require(action in ('up','down','select','back'),'network-menu-bounded-input')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
        method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in r,'network-menu-input')
def ready_settings(installed):
    xbmc.executebuiltin('ActivateWindow(Settings)')
    until(lambda:xbmcgui.getCurrentWindowId()==10004,'network-menu-settings-window')
    n=206 if installed else 200
    xbmc.executebuiltin('Control.SetFocus('+str(n)+')');until(lambda:focus(n),'network-menu-settings-focus')
def launch(installed):
    if installed:press('select')
    else:xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+PIN+',diagnostics)')
    until(lambda:bool(homeprop('MenuOpen')) and focus(1421),'network-menu-open')

result=dict(passed=False,checks_enforced=True,production_changed=False,logs_opened=False)
cp=None
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==2 and sys.argv[1] in ('staged','installed'),
        'network-menu-test-arguments')
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not homeprop('MenuOpen') and
        not homeprop('PreviewWindow'),'network-menu-test-idle-home')
    baseline=guard.snapshot();original=hashlib.sha256(TARGET.read_bytes()).hexdigest()
    cp=Path('/storage/.aster-checkpoints')/('aster-network-settings-native-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    installed=sys.argv[1]=='installed';source_focus=206 if installed else 200
    ready_settings(installed);launch(installed)
    xbmc.sleep(600);xbmc.executebuiltin('TakeScreenshot('+str(cp/'diagnostics-menu.png')+')');xbmc.sleep(700)
    require(xbmcgui.getCurrentWindowId()==10004,'network-menu-not-over-settings')
    if xbmc.getCondVisibility('System.HasAddon(script.logviewer)'):
        press('down');until(lambda:focus(1422),'network-menu-log-focus')
        press('up');until(lambda:focus(1421),'network-menu-network-focus')
    press('back');until(lambda:not homeprop('MenuOpen') and focus(source_focus),'network-menu-back-focus')
    xbmc.sleep(400);launch(installed);press('select')
    until(lambda:homeprop('PreviewWindow') and xbmc.getInfoLabel('Window.Property(NetworkPreview.Ready)')=='true',
        'network-menu-network-ready')
    require(not homeprop('MenuOpen') and focus(200),'network-menu-dialog-left-open')
    require(xbmc.getInfoLabel('Window.Property(NetworkPreview.ServiceRequests)')=='0','network-menu-probed-on-entry')
    press('back');until(lambda:not homeprop('PreviewWindow') and xbmcgui.getCurrentWindowId()==10004 and focus(source_focus),
        'network-menu-network-back-context')
    xbmc.sleep(400);launch(installed)
    r=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in r,'network-menu-home-input')
    xbmc.sleep(350)
    require(homeprop('MenuOpen') and xbmcgui.getCurrentWindowId()==10004,'network-menu-modal-boundary')
    press('back');until(lambda:not homeprop('MenuOpen') and focus(source_focus),'network-menu-home-back')
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}')
    until(lambda:xbmcgui.getCurrentWindowId()==10000,'network-menu-home-after-back')
    xbmc.sleep(400);ready_settings(installed);launch(installed);press('select')
    until(lambda:bool(homeprop('PreviewWindow')),'network-menu-second-network')
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}')
    until(lambda:not homeprop('PreviewWindow') and xbmcgui.getCurrentWindowId()==10000,'network-menu-network-home')
    require(guard.idle() and baseline==guard.snapshot() and hashlib.sha256(TARGET.read_bytes()).hexdigest()==original,
        'network-menu-preservation')
    result.update(passed=True,mode=sys.argv[1],compact_menu=True,log_action_retained=True,back_focus=True,
        settings_network_return=True,no_probes_on_entry=True,menu_modal_home_boundary=True,home_after_back=True,network_home_exit=True,
        settings_unchanged=True,av_settings_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
    result['failure_navigation']=dict(window=xbmcgui.getCurrentWindowId(),
        current_control=xbmc.getInfoLabel('System.CurrentControlId'),focus200=focus(200),focus206=focus(206),
        menu_open=bool(homeprop('MenuOpen')),network_open=bool(homeprop('PreviewWindow')))
finally:
    try:
        if guard.idle() and (homeprop('MenuOpen') or homeprop('PreviewWindow')):
            press('back');xbmc.sleep(400)
        if guard.idle() and xbmcgui.getCurrentWindowId()==10004:
            xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}')
    except Exception:result['cleanup_required']=True
    if cp is not None:(cp/'native.json').write_text(json.dumps(result,indent=2)+'\n')
