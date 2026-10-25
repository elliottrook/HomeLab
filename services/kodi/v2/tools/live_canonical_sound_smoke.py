"""Idle approved-box sound smoke; no media, settings, input or volume writes."""
import json,os,re,time
from pathlib import Path
import xbmc
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename in ('AsterTV','AsterTVProd'),'approved-host-only')
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Settings.GetSettingValue'),'read-only-rpc')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in r,'rpc-error');return r['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
base=Path('/storage/.aster-checkpoints/aster-canonical-pcm32-20261025')
result={};log=Path('/storage/.kodi/temp/kodi.log');stat=log.stat()
try:
    require(idle(),'idle-empty-required')
    theme=rpc('Settings.GetSettingValue',dict(setting='lookandfeel.soundskin'))['value']
    require(theme=='resource.uisounds.asterhome','canonical-theme-required')
    for name,gap in (('nav-left.wav',340),('select.wav',160),('back.wav',340),('notify.wav',480)):
        xbmc.playSFX('/storage/.kodi/addons/resource.uisounds.asterhome/resources/'+name,useCached=False)
        xbmc.sleep(gap)
    for _ in range(6):
        xbmc.playSFX('/storage/.kodi/addons/resource.uisounds.asterhome/resources/nav-left.wav',useCached=True)
        xbmc.sleep(80)
    xbmc.sleep(600)
    require(log.stat().st_ino==stat.st_ino and log.stat().st_size>=stat.st_size,'log-rotation-retry-later')
    with log.open('rb') as handle:handle.seek(stat.st_size);lines=handle.read(1000000).decode(errors='replace').splitlines()
    errors=sum(bool(re.search(r'\b(ERROR|FATAL)\b',line,re.I)) and any(word in line for word in
        ('Sound','sound','Wave','WAV','ActiveAE','nav-left.wav','select.wav','back.wav','notify.wav')) for line in lines)
    require(errors==0,'sound-engine-error')
    require(idle(),'media-state-changed')
    result=dict(passed=True,unique_cues_exercised=4,rapid_repeat_requests=6,sound_engine_errors=errors,
        no_media_or_settings_writes=True,audible_confirmation=False)
except Exception as error:result=dict(passed=False,code=str(error))
path=base/('native-smoke-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
