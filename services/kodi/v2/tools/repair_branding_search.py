"""Complete review9's missing native Search overlay; guarded exact-file repair."""
import fcntl,hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
def sha(data):return hashlib.sha256(data).hexdigest()
require(os.uname().nodename=='AsterTV','hp-only')
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
disabled_mode='--settings-disabled' in sys.argv
settings_mode='--settings' in sys.argv or disabled_mode
root=Path('/storage/.aster-checkpoints/aster-branding-settings-disabled-20261025' if disabled_mode else '/storage/.aster-checkpoints/aster-branding-settings-repair-20261025' if settings_mode else '/storage/.aster-checkpoints/aster-branding-search-repair-20261025')
target=Path('/storage/.kodi/addons/skin.asterhome/1080i/'+('Settings.xml' if settings_mode else 'custom_1127_search.xml'))
source=Path('/storage/.aster-staging/aster-branding-settings-disabled/Settings.xml' if disabled_mode else '/storage/.aster-staging/aster-branding-settings-repair/Settings.xml' if settings_mode else '/storage/.aster-staging/aster-global-search-ui22/overlay/custom_1127_search.xml')
pair=('c587268c5c972f15f4d1f169db90f3aea48428010fc93d3e68ac0c1f81f4234a','09a98be3b9ecddf185f61fdfb561bf9e68c4be123816e4f78ecc34210e136ab4') if disabled_mode else ('56e385bb237e3e2a8edc1f6d118758d5da0b385b5b7b3dc97be25da7fc7ef069','c587268c5c972f15f4d1f169db90f3aea48428010fc93d3e68ac0c1f81f4234a') if settings_mode else ('f17ca8db0ffa4bd923ae2649d3db94005c246553b00e028082d029703b9715c8','6f1fbe60d9d1ef9187ad0524602268145c9412c5d2c886c104243103b692e55e')
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Settings.GetSettings'),'read-only-rpc')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in r,'rpc-failed');return r['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
result=dict(passed=False)
try:
    require(not root.exists() and idle() and not xbmcgui.Window(10000).getProperty('AsterSearch.Ready'),'idle-unowned-required')
    require(not target.is_symlink() and not source.is_symlink(),'no-symlinks')
    before=target.read_bytes();after=source.read_bytes();settings=rpc('Settings.GetSettings')
    require((sha(before),sha(after))==pair,'exact-overlay-pair')
    root.mkdir(mode=0o700);(root/'before.xml').write_bytes(before)
    require((root/'before.xml').read_bytes()==before and idle(),'checkpoint-and-idle')
    temp=target.with_suffix('.branding-tmp');temp.write_bytes(after);os.replace(temp,target)
    require(target.read_bytes()==after and rpc('Settings.GetSettings')==settings and idle(),'repair-preservation')
    result.update(passed=True,sha256=sha(after),before_sha256=sha(before),settings_unchanged=True,only_skin_overlay=True,member=target.name)
    xbmc.executebuiltin('ReloadSkin')
except Exception as error:result['code']=str(error) if isinstance(error,RuntimeError) else type(error).__name__
finally:
    report=Path('/storage/.aster-checkpoints/aster-review9-20261025')/('native-repair-'+str(time.time_ns())+'.json')
    report.write_text(json.dumps(result,indent=2));report.chmod(0o600)
    if result['passed']:(root/'verified.json').write_text(json.dumps(result,indent=2))
    os.close(lock)
