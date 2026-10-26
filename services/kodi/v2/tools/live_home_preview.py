"""HP local-file Home preview: navigation and no-effect preservation proof."""
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard


def require(value,code):
    if not value:raise RuntimeError(code)
def until(check,code,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(60)
    raise RuntimeError(code)
def prop(key):return xbmc.getInfoLabel('Window.Property(HomePreview.'+key+')')
def opened():return bool(xbmcgui.Window(10000).getProperty('AsterHome.PreviewWindow'))
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def press(action):
    require(action in ('left','right','up','down','select','back'),'home-preview-bounded-input')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
        method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in reply,'home-preview-input')
def setfocus(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
    until(lambda:focus(identity),'home-preview-focus-'+str(identity))
def feed_hash(path):
    if not path.exists():return None
    require(not any(p.is_symlink() for p in (path,*path.parents)),'home-preview-feed-linked')
    fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        metadata=os.fstat(stream.fileno())
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_size<=262144,'home-preview-feed-regular')
        raw=stream.read(262145)
    require(len(raw)<=262144,'home-preview-feed-size')
    return hashlib.sha256(raw).hexdigest()


result=dict(passed=False,checks_enforced=True,production_changed=False)
checkpoint=None
try:
    require(os.uname().nodename=='AsterTV' and guard.idle() and
        xbmcgui.getCurrentWindowId()==10000 and not opened(),'home-preview-home-idle')
    require(len(sys.argv)==2 and re.fullmatch('[0-9a-f]{64}',sys.argv[1]),'home-preview-external-pin')
    pin=sys.argv[1];raw=(ROOT/'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==pin,'home-preview-manifest-pin')
    manifest=json.loads(raw)
    require(len(manifest['files'])==5,'home-preview-five-members')
    for row in manifest['files']:
        require(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],'home-preview-member')
    spec=importlib.util.spec_from_file_location('home_preview_source_entry',ROOT/'default.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source);source.verify(pin)
    sys.path.insert(0,str(ROOT/'resources/lib'))
    from home_preview_source import read_payload
    from home_dashboard_model import project
    expected=project(read_payload(source.FEED),datetime.now(timezone.utc))
    original_feed=feed_hash(source.FEED)
    before=guard.snapshot()
    checkpoint=Path('/storage/.aster-checkpoints')/('aster-home-preview-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    (checkpoint/'before.json').write_text(json.dumps(before))
    press('left')
    until(lambda:not xbmc.getCondVisibility('System.ScreenSaverActive'),'home-preview-wake')
    setfocus(136)
    xbmc.sleep(250)
    result['launch_focus']=xbmcgui.Window(10000).getFocusId()
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+pin+')')
    until(lambda:opened() and prop('Ready')=='true' and focus(301),'home-preview-ready')
    require(prop('State')==expected.state,'home-preview-freshness')
    for index,group in enumerate(expected.groups):
        require(prop('Group'+str(index))==group.state,'home-preview-group-state')
        require(xbmc.getInfoLabel('Control.GetLabel('+str(401+index)+')')==group.summary,'home-preview-visible-summary')
    for action,identity in (('right',302),('down',304),('up',302),('left',301),
            ('down',303),('right',304),('down',304)):
        press(action);until(lambda:focus(identity),'home-preview-adjacent-navigation')
    press('select')
    until(lambda:xbmc.getInfoLabel('Control.GetLabel(503)').startswith('Read-only status'),'home-preview-no-action-notice')
    require(guard.idle(),'home-preview-card-started-media')
    setfocus(201);press('select');xbmc.sleep(400)
    require(prop('State')==expected.state and feed_hash(source.FEED)==original_feed,'home-preview-reload-mutated-source')
    setfocus(301);xbmc.sleep(1000)
    if expected.state!='fresh':
        xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'home-preview.png')+')')
        xbmc.sleep(500)
    else:result['capture_omitted_private_values']=True
    press('back')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000 and focus(136),'home-preview-back-context')
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+pin+')')
    until(lambda:opened() and prop('Ready')=='true','home-preview-reopen')
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in reply,'home-preview-home-input')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000,'home-preview-home-exit')
    require(guard.idle() and guard.snapshot()==before and feed_hash(source.FEED)==original_feed,'home-preview-preservation')
    result.update(passed=True,source_state=expected.state,group_states=[g.state for g in expected.groups],
        adjacent_navigation=True,bottom_no_wrap=True,read_only_notice=True,local_reload=True,
        feed_unchanged=True,back_focus=True,home_exit=True,settings_navigation_unchanged=True)
except Exception as error:
    code=str(error)
    result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
    result['window']=xbmcgui.getCurrentWindowId()
    if result['window']==10000:result['returned_home_focus']=xbmcgui.Window(10000).getFocusId()
finally:
    if opened() and guard.idle():
        press('back');until(lambda:not opened(),'home-preview-cleanup')
    result['idle_empty']=guard.idle()
    if checkpoint is not None:(checkpoint/'native.json').write_text(json.dumps(result,indent=2))
