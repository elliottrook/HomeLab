"""HP real local configuration and explicit offline-demo native proof."""
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
def opened():return bool(xbmcgui.Window(10000).getProperty('AsterNetwork.PreviewWindow'))
def prop(key):return xbmc.getInfoLabel('Window.Property(NetworkPreview.'+key+')')
def focus(n):return xbmc.getCondVisibility('Control.HasFocus('+str(n)+')')
def press(action):
    require(action in ('left','right','select','back'),'network-test-bounded-input')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
        method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in reply,'network-test-input')
def stable(facts):
    return (facts.state,facts.interface,facts.link,facts.addresses,facts.gateway,facts.dns,facts.notes)


result=dict(passed=False,checks_enforced=True,production_changed=False,network_changed=False)
checkpoint=None
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==2 and guard.idle() and
        xbmcgui.getCurrentWindowId()==10000 and not opened(),'network-test-home-idle')
    spec=importlib.util.spec_from_file_location('network_entry',ROOT/'default.py')
    entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry);entry.verify(sys.argv[1])
    sys.path.insert(0,str(ROOT));import network_diagnostics as network
    baseline=network.collect();settings=guard.snapshot()
    checkpoint=Path('/storage/.aster-checkpoints')/('aster-network-preview-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    press('left');xbmc.executebuiltin('Control.SetFocus(136)')
    until(lambda:focus(136),'network-test-source-focus');xbmc.sleep(250)
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+sys.argv[1]+')')
    until(lambda:opened() and prop('Ready')=='true' and focus(200) and
        xbmc.getInfoLabel('Control.GetLabel(501)')==baseline.state,'network-test-real-ready')
    require(prop('Reachability')=='Not tested' and prop('Revision')=='1','network-test-unproven-reachability')
    require(prop('ServiceRequests')=='0','network-test-probed-on-open')
    xbmc.sleep(2500);require(prop('Revision')=='1','network-test-background-refresh')
    press('select');until(lambda:prop('Ready')=='true' and prop('Revision')=='2','network-test-manual-refresh')
    require(focus(200),'network-test-refresh-stole-focus')
    require(prop('ServiceRequests')=='0','network-test-local-refresh-probed')
    press('right');until(lambda:focus(203),'network-test-service-button-focus')
    press('select')
    until(lambda:prop('ServiceRevision')=='1' and prop('ServiceStatus')=='complete','network-test-explicit-check')
    require(prop('ServiceRequests')=='2' and focus(203),'network-test-service-request-count')
    result['observed_http_statuses']=[prop('ServiceHTTP0'),prop('ServiceHTTP1')]
    require(prop('Reachability')=='Only media HTTP endpoints checked','network-test-media-only-claim')
    xbmc.sleep(1000);xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'local-network.png')+')');xbmc.sleep(700)
    press('right');until(lambda:focus(201),'network-test-back-button-focus')
    press('select');until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000 and focus(136),'network-test-back-context')
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+sys.argv[1]+',offline-demo)')
    until(lambda:opened() and prop('Ready')=='true' and prop('State')=='No local IPv4 address' and
        'NOT changed' in xbmc.getInfoLabel('Control.GetLabel(504)'),'network-test-offline-demo')
    require(prop('Reachability')=='Not tested','network-test-offline-reachability')
    require(prop('ServiceRequests')=='0' and prop('ServiceHTTP0')=='none' and prop('ServiceHTTP1')=='none',
        'network-test-offline-probed')
    xbmc.sleep(1000);xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'offline-demo.png')+')');xbmc.sleep(700)
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in reply,'network-test-home-input')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000,'network-test-home-exit')
    require(guard.idle() and settings==guard.snapshot() and stable(network.collect())==stable(baseline),
        'network-test-preservation')
    result.update(passed=True,real_local_facts=True,no_background_collection=True,
        manual_refresh=True,focus_preserved=True,back_context=True,offline_demo=True,
        honest_reachability=True,home_exit=True,settings_unchanged=True,local_configuration_unchanged=True)
    result.update(no_probes_on_open=True,no_probes_on_local_refresh=True,
        explicit_media_checks=True,offline_demo_no_probes=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    try:
        if opened() and guard.idle():press('back');until(lambda:not opened(),'network-test-close')
    except Exception:result.update(passed=False,cleanup_required=True)
    result['idle_empty']=guard.idle()
    if checkpoint is not None:(checkpoint/'native.json').write_text(json.dumps(result,indent=2)+'\n')
