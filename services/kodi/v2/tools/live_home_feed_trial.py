"""HP one-shot Home publication: fresh UI, real expiry, exact rollback; no camera."""
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
PREVIEW=Path('/storage/.aster-staging/aster-home-preview2')
PREVIEW_PIN='f3e4cdbb3e391bd2380d1f84217a9d9f882ff9dbabcc2d0625c3af0518be0a4e'
FEED=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home.json')
CHECKPOINT=Path('/storage/.aster-checkpoints')/ROOT.name
BEFORE='a975c8c68dc5cf5d70c12530fb0bba60b89b78eb06d081f95ea6d97331b5b6cd'


def require(ok,code):
    if not ok:raise RuntimeError(code)
def prop(name):return xbmc.getInfoLabel('Window.Property(HomePreview.'+name+')')
def opened():return bool(xbmcgui.Window(10000).getProperty('AsterHome.PreviewWindow'))
def focus(n):return xbmc.getCondVisibility('Control.HasFocus('+str(n)+')')
def until(check,code,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(code)
def press(name):
    require(name in ('left','right','down','up','back','select'),'home-trial-bounded-input')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
        method='Input.ExecuteAction',params=dict(action=name)))))
    require('error' not in reply,'home-trial-input')
def status(value):
    raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    path=ROOT/'progress.json'
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(raw)


result=dict(passed=False,checks_enforced=True,production_changed=False)
locked=None;checkpointed=False;guard=None;publication=None
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==3,'home-trial-host-arguments')
    require(re.fullmatch('aster-home-feed-trial[1-9][0-9]?',ROOT.name),'home-trial-fixed-stage-family')
    pin,candidate_pin=sys.argv[1:]
    require(all(re.fullmatch('[0-9a-f]{64}',p) for p in (pin,candidate_pin)),'home-trial-pins')
    manifest_raw=(ROOT/'manifest.json').read_bytes()
    require(hashlib.sha256(manifest_raw).hexdigest()==pin,'home-trial-manifest')
    manifest=json.loads(manifest_raw)
    require(manifest['kind']=='hp-home-feed-trial.v1' and len(manifest['files'])==5
        and {row['path'] for row in manifest['files']}=={'live_home_feed_trial.py',
            'home_publication.py','home_delivery.py','home_dashboard_model.py','home_freshness.py'}
        and manifest.get('one_shot') is True and manifest.get('restore_original') is True
        and manifest.get('production') is False and manifest.get('automatic_refresh') is False,
        'home-trial-contract')
    for row in manifest['files']:
        path=ROOT/row['path']
        require(not any(p.is_symlink() for p in (path,*path.parents)) and
            hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],'home-trial-member')
    locked=os.open(str(ROOT/'trial.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    fcntl.flock(locked,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(not CHECKPOINT.exists(),'home-trial-already-consumed')
    sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
    import deploy_startup as guard
    sys.path.insert(0,str(ROOT))
    import home_publication as publication
    from home_dashboard_model import project
    def ready():return guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not opened()
    require(ready(),'home-trial-home-idle')
    snapshot=guard.snapshot()
    raw,_=publication.read_private(ROOT/'candidate.json')
    require(publication.digest(raw)==candidate_pin,'home-trial-candidate-pin')
    payload=publication.validate(raw,datetime.now(timezone.utc))
    spec=importlib.util.spec_from_file_location('home_trial_legacy',
        '/storage/.kodi/addons/skin.asterhome/tools/hub_feeds.py')
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
    require(legacy.home_dashboard(payload)['CameraStatus']=='No reviewed camera','home-trial-legacy-compatibility')
    require(hashlib.sha256((PREVIEW/'manifest.json').read_bytes()).hexdigest()==PREVIEW_PIN,'home-trial-preview-pin')
    preview_spec=importlib.util.spec_from_file_location('home_trial_preview',PREVIEW/'default.py')
    preview=importlib.util.module_from_spec(preview_spec);preview_spec.loader.exec_module(preview);preview.verify(PREVIEW_PIN)
    publication.checkpoint(FEED,CHECKPOINT,BEFORE);checkpointed=True
    publication.apply(FEED,CHECKPOINT,raw,candidate_pin,ready)
    result.update(phase='applied',candidate_sha256=candidate_pin,legacy_compatible=True)
    status(result)
    press('left');xbmc.executebuiltin('Control.SetFocus(136)');until(lambda:focus(136),'home-trial-launch-focus')
    xbmc.sleep(250)
    xbmc.executebuiltin('RunScript('+str(PREVIEW/'default.py')+','+PREVIEW_PIN+')')
    until(lambda:opened() and prop('Ready')=='true' and prop('State')=='fresh','home-trial-fresh-display')
    expected=project(payload,datetime.now(timezone.utc))
    require([prop('Group'+str(i)) for i in range(4)]==[g.state for g in expected.groups],
        'home-trial-group-bindings')
    def summaries():
        return [xbmc.getInfoLabel('Control.GetLabel('+str(401+i)+')')==g.summary
            for i,g in enumerate(expected.groups)]
    result['initial_summary_matches']=summaries()
    until(lambda:all(summaries()),'home-trial-visible-summary')
    for action,n in (('right',302),('down',304),('left',303),('up',301)):
        press(action);until(lambda:focus(n),'home-trial-adjacent-navigation')
    result.update(phase='waiting-real-expiry',fresh_ui=True,camera_unconnected=True,
        timer_unconnected=True,private_capture_omitted=True,wait_started=time.time())
    status(result)
    deadline=time.monotonic()+625
    while prop('State')!='stale':
        require(time.monotonic()<deadline,'home-trial-expiry-timeout')
        require(guard.idle() and opened(),'home-trial-interrupted')
        xbmc.sleep(500)
    require(all(prop('Group'+str(i))=='stale' for i in range(4)),'home-trial-expired-groups')
    require(all(xbmc.getInfoLabel('Control.GetLabel('+str(401+i)+')')=='Values unavailable'
        for i in range(4)),'home-trial-expired-visible-summary')
    require(publication.digest(publication.read_private(FEED)[0])==candidate_pin,'home-trial-feed-modified')
    press('back');until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000 and focus(136),'home-trial-back')
    require(guard.snapshot()==snapshot and guard.idle(),'home-trial-settings-preservation')
    result.update(passed=True,phase='expiry-verified',real_elapsed_expiry=True,
        no_source_redating=True,adjacent_navigation=True,back_focus=True,settings_unchanged=True)
except Exception as error:
    code=str(error)
    result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    try:
        if guard is not None and opened() and guard.idle():
            press('back');until(lambda:not opened(),'home-trial-close')
    except Exception:
        result.update(passed=False,ui_cleanup_failed=True)
    if checkpointed:
        try:
            publication.restore(FEED,CHECKPOINT)
            result['original_feed_restored']=publication.digest(publication.read_private(FEED)[0])==BEFORE
        except Exception as error:
            result.update(passed=False,rollback_required=True,rollback_code=type(error).__name__)
    if guard is not None:result['idle_empty']=guard.idle()
    status(result)
    if locked is not None:os.close(locked)
