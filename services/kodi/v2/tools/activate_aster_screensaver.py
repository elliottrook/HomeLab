"""Replace recurrent native Dim with the already-verified HP Aster saver."""
import hashlib,json,os,re,time
from pathlib import Path
import xbmc,xbmcaddon,xbmcgui

ADDON='screensaver.asterhome.v2lab';EXPECTED={
'addon.xml':'bfa94e07111821636b863ca048767b73a0fa028bf69dc1669391b90589ade1b9',
'default.py':'54aa8b007fbcc519b88ba831d18b276b4e34473c0cd995f1a7a4caf174047f4d'}
def require(ok,code):
    if not ok:raise RuntimeError(code)
def rpc(method,params):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Settings.GetSettingValue','Settings.SetSettingValue'),'aster-saver-rpc-boundary')
    if method.startswith('Settings.'):
        require(params.get('setting') in ('screensaver.mode','screensaver.time'),'aster-saver-setting-boundary')
        if method=='Settings.SetSettingValue':require(params=={'setting':'screensaver.mode','value':ADDON},'aster-saver-write-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    require('error' not in reply,'aster-saver-rpc');return reply.get('result')
def idle():return not rpc('Player.GetActivePlayers',{}) and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def setting(name):return rpc('Settings.GetSettingValue',{'setting':name})['value']

cp=None;result=dict(passed=False,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and len(__import__('sys').argv)==1 and idle()
            and not xbmc.getCondVisibility('System.ScreenSaverActive'),'aster-saver-hp-idle-only')
    root=Path('/storage/.kodi/addons')/ADDON
    for name,wanted in EXPECTED.items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==wanted,'aster-saver-file-drift')
    addon=xbmcaddon.Addon(ADDON);before=dict(mode=setting('screensaver.mode'),minutes=setting('screensaver.time'),presentation=addon.getSettingString('presentation'))
    require(before['mode']=='screensaver.xbmc.builtin.dim' and before['minutes']==3,'aster-saver-baseline-drift')
    cp=Path('/storage/.aster-checkpoints')/('aster-saver-activation-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    baseline=cp/'before.json';baseline.write_text(json.dumps(before,sort_keys=True)+'\n');baseline.chmod(0o600)
    addon.setSettingString('presentation','aster')
    require(rpc('Settings.SetSettingValue',{'setting':'screensaver.mode','value':ADDON}) is True,'aster-saver-mode-write')
    after=dict(mode=setting('screensaver.mode'),minutes=setting('screensaver.time'),presentation=addon.getSettingString('presentation'))
    require(after==dict(mode=ADDON,minutes=3,presentation='aster'),'aster-saver-post-state')
    result.update(passed=True,before=before,after=after,timeout_preserved=True,installed_files_verified=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if cp:
        path=cp/'result.json';path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
