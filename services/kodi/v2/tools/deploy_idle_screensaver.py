"""Register/disable only the new unselected HP idle pilot; preserve all others."""
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from idle_screensaver_install import IDENTITY,CHECKPOINT,inspect,prepare,verify_files,mark,require
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
KEYS=('screensaver.mode','screensaver.time','screensaver.usedimonpause',
    'powermanagement.displaysoff','powermanagement.shutdowntime','powermanagement.shutdownstate')
def rpc(method,params):
    require(method in ('Addons.GetAddons','Addons.SetAddonEnabled','Settings.GetSettingValue'),'idle-deploy-rpc-boundary')
    if method=='Addons.SetAddonEnabled':require(params.get('addonid')==IDENTITY,'idle-deploy-addon-boundary')
    if method=='Settings.GetSettingValue':require(params.get('setting') in KEYS,'idle-deploy-setting-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    require('error' not in reply,'idle-deploy-rpc');return reply.get('result',{})
def inventory():
    rows=rpc('Addons.GetAddons',dict(enabled='all',properties=['enabled','version']))['addons']
    require(len(rows)<2000,'idle-deploy-inventory-size')
    result={}
    for r in rows:
        require(re.fullmatch('[a-zA-Z0-9_.-]{1,160}',r['addonid']) and type(r['enabled']) is bool and
            isinstance(r['version'],str) and len(r['version'])<100,'idle-deploy-inventory-shape')
        require(r['addonid'] not in result,'idle-deploy-inventory-duplicate')
        result[r['addonid']]=dict(enabled=r['enabled'],version=r['version'])
    return result
def settings():return {k:rpc('Settings.GetSettingValue',dict(setting=k))['value'] for k in KEYS}
def idle():
    return (guard.idle() and xbmcgui.getCurrentWindowId()==10000 and
        not xbmcgui.Window(10000).getProperty('AsterIdle.Window') and
        not xbmcgui.Window(10000).getProperty('AsterNetwork.MenuOpen'))

if __name__=='__main__':
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==3,'idle-deploy-hp-arguments')
    mode,pin=sys.argv[1:3]
    require(mode in ('install','verify','disable') and re.fullmatch('[0-9a-f]{64}',pin),'idle-deploy-arguments')
    inspect(ROOT,pin)
    lock=os.open(str(ROOT/'deploy.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    result=dict(passed=False,production_changed=False)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(idle(),'idle-deploy-home-idle-required')
        av=guard.snapshot();current=settings();before=inventory()
        require(current['screensaver.mode']=='screensaver.xbmc.builtin.dim','idle-deploy-original-dim-required')
        if mode=='install':
            baseline=prepare(ROOT,Path('/storage'),pin,dict(settings=current,inventory=before),idle=idle)
            require(current==baseline['settings'],'idle-deploy-baseline-settings-drift')
            require({k:v for k,v in before.items() if k!=IDENTITY}==baseline['inventory'],'idle-deploy-foreign-addon-drift')
            xbmc.executebuiltin('UpdateLocalAddons')
            end=time.monotonic()+8
            while time.monotonic()<end:
                after=inventory()
                if IDENTITY in after:break
                xbmc.sleep(150)
            require(IDENTITY in after and idle(),'idle-deploy-not-registered')
            if not after[IDENTITY]['enabled']:
                rpc('Addons.SetAddonEnabled',dict(addonid=IDENTITY,enabled=True));xbmc.sleep(300)
            mark(ROOT,Path('/storage'),pin,'registered')
        else:
            _,baseline,_=verify_files(ROOT,Path('/storage'),pin)
            if mode=='disable':
                rpc('Addons.SetAddonEnabled',dict(addonid=IDENTITY,enabled=False));xbmc.sleep(300)
                mark(ROOT,Path('/storage'),pin,'disabled')
        verify_files(ROOT,Path('/storage'),pin);after=inventory()
        require({k:v for k,v in after.items() if k!=IDENTITY}==baseline['inventory'],'idle-deploy-other-addons-changed')
        require(after.get(IDENTITY,{}).get('version')=='0.1.0','idle-deploy-version')
        if mode in ('install','disable'):require(after[IDENTITY]['enabled']==(mode=='install'),'idle-deploy-enable-state')
        require(settings()==baseline['settings']==current and guard.snapshot()==av and idle(),'idle-deploy-preservation')
        result.update(passed=True,mode=mode,files_verified=7,pilot_enabled=after[IDENTITY]['enabled'],
            pilot_selected=False,other_addons_unchanged=True,settings_unchanged=True,av_settings_unchanged=True,
            checkpoint_verified=True,idle_empty=True)
    except (OSError,ValueError,KeyError,RuntimeError) as error:
        code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
    finally:os.close(lock)
    path=ROOT/('deploy-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
