"""HP synthetic-generation proof; writes only this stage's labelled fixture."""
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
FIXTURE=ROOT/'synthetic-home.json'
REAL=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home.json')
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard


def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(code)
def prop(key):return xbmc.getInfoLabel('Window.Property('+key+')')
def opened():return bool(xbmcgui.Window(10000).getProperty('AsterHome.PreviewWindow'))
def focus(n):return xbmc.getCondVisibility('Control.HasFocus('+str(n)+')')
def press(action):
    require(action in ('left','right','up','down','select','back'),'refresh-test-bounded-input')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
        method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in reply,'refresh-test-input')
def setfocus(n):
    xbmc.executebuiltin('Control.SetFocus('+str(n)+')')
    until(lambda:focus(n),'refresh-test-focus')
def digest(raw):return hashlib.sha256(raw).hexdigest()


result=dict(passed=False,checks_enforced=True,synthetic=True,production_changed=False)
checkpoint=None;owned=None;initial=None


def write(raw):
    global owned
    require(not FIXTURE.is_symlink(),'refresh-test-linked-fixture')
    require((not FIXTURE.exists() and owned is None) or
        (FIXTURE.exists() and digest(FIXTURE.read_bytes())==owned),'refresh-test-foreign-fixture')
    fd,name=tempfile.mkstemp(prefix='.synthetic-',dir=ROOT)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(name,FIXTURE);owned=digest(raw)
    finally:
        if os.path.exists(name):os.unlink(name)


def remove():
    global owned
    require(not FIXTURE.is_symlink() and digest(FIXTURE.read_bytes())==owned,'refresh-test-cleanup-drift')
    FIXTURE.unlink();owned=None


try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==2 and
        re.fullmatch('aster-home-refresh-preview[1-9][0-9]?',ROOT.name),'refresh-test-hp-stage')
    require(not FIXTURE.exists() and not FIXTURE.is_symlink() and guard.idle() and
        xbmcgui.getCurrentWindowId()==10000 and not opened(),'refresh-test-home-idle')
    spec=importlib.util.spec_from_file_location('refresh_entry',ROOT/'default.py')
    entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry);entry.verify(sys.argv[1])
    initial=digest(REAL.read_bytes());settings=guard.snapshot()
    checkpoint=Path('/storage/.aster-checkpoints')/('aster-home-refresh-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    now=datetime.now(timezone.utc)
    def payload(source_age,publication_age,light=True):
        return dict(schema_version=1,generated_at=(now-timedelta(seconds=publication_age)).isoformat(),
            source_updated_at=(now-timedelta(seconds=source_age)).isoformat(),
            snapshot=dict(schema_version=3,snapshot_id='ha-home-pilot-v3',
                lights=[dict(alias='laundry lights',state='off')] if light else [],
                temperatures=[dict(alias='closet temperature',value=24.5,unit='°C')],
                weather=[dict(alias='home weather',condition='sunny',temperature=15,unit='°C',humidity=60)],
                rooms=[],entities=[],timers=[],media_providers=[]))
    first=json.dumps(payload(90,80)).encode();second=json.dumps(payload(30,20,False)).encode()
    write(first)
    press('left');setfocus(136);xbmc.sleep(250)
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+sys.argv[1]+',synthetic)')
    until(lambda:opened() and prop('HomePreview.State')=='fresh' and focus(301),'refresh-test-initial')
    setfocus(304)
    until(lambda:prop('HomeRefresh.Reads')=='1','refresh-test-first-read')
    xbmc.sleep(4500)
    require(prop('HomeRefresh.Reads')=='1' and focus(304),'refresh-test-repeated-whole-file-read')
    write(second)
    until(lambda:prop('HomeRefresh.Generations')=='2' and
        xbmc.getInfoLabel('Control.GetLabel(401)')=='No reviewed values','refresh-test-new-generation')
    require(focus(304),'refresh-test-update-stole-focus')
    reads=int(prop('HomeRefresh.Reads'));write(second)
    until(lambda:int(prop('HomeRefresh.Reads'))==reads+1,'refresh-test-duplicate-read')
    require(prop('HomeRefresh.Generations')=='2' and focus(304),'refresh-test-duplicate-reset')
    setfocus(201);press('select')
    until(lambda:int(prop('HomeRefresh.Reads'))==reads+2,'refresh-test-manual-reload')
    require(prop('HomeRefresh.Generations')=='2','refresh-test-manual-generation')
    setfocus(304);write(b'{')
    until(lambda:prop('HomePreview.State')=='invalid','refresh-test-malformed')
    require(focus(304),'refresh-test-invalid-stole-focus')
    remove();until(lambda:prop('HomePreview.State')=='missing','refresh-test-missing')
    write(first)
    until(lambda:prop('HomeRefresh.LoadStatus')=='older-generation' and
        prop('HomePreview.State')=='invalid','refresh-test-replay')
    write(json.dumps(payload(1200,0)).encode())
    until(lambda:prop('HomePreview.State')=='stale','refresh-test-old-source')
    recovery=json.dumps(payload(0,0,False)).encode();write(recovery)
    until(lambda:prop('HomePreview.State')=='fresh' and prop('HomeRefresh.Generations')=='3','refresh-test-recovery')
    require(focus(304),'refresh-test-recovery-stole-focus')
    xbmc.sleep(1000)
    require('NOT household readings' in xbmc.getInfoLabel('Control.GetLabel(504)'),
        'refresh-test-synthetic-banner')
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'synthetic-refresh.png')+')');xbmc.sleep(800)
    press('back');until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000 and focus(136),'refresh-test-back')
    remove()
    # Independent default-mode opening must use the unchanged real feed, not the fixture.
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+sys.argv[1]+')')
    until(lambda:opened() and prop('HomePreview.State')=='stale','refresh-test-default-source')
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in reply,'refresh-test-home-input')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000,'refresh-test-home-exit')
    require(digest(REAL.read_bytes())==initial and guard.snapshot()==settings and guard.idle(),
        'refresh-test-preservation')
    result.update(passed=True,unchanged_file_cached=True,new_generation=True,duplicate_cached=True,
        manual_local_reload=True,malformed_hidden=True,missing_hidden=True,replay_rejected=True,
        old_source_hidden=True,recovery=True,focus_preserved=True,back_context=True,home_exit=True,
        real_feed_unchanged=True,settings_unchanged=True,fixture_removed=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    try:
        if opened() and guard.idle():press('back');until(lambda:not opened(),'refresh-test-close')
        if owned is not None:remove()
    except Exception:result.update(passed=False,cleanup_required=True)
    result['idle_empty']=guard.idle()
    if initial is not None:result['real_feed_unchanged']=digest(REAL.read_bytes())==initial
    if checkpoint is not None:(checkpoint/'native.json').write_text(json.dumps(result,indent=2)+'\n')
