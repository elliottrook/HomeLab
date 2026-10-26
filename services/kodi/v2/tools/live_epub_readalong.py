"""Native HP proof for narrated EPUB page-follow, resume and cleanup."""
import hashlib,json,os,re,sys,time
from pathlib import Path
import xbmc,xbmcgui

ROOT=Path('/storage/.aster-staging/aster-epub-readalong-word-groups5')
STATE=Path('/storage/.aster-state/aster-epub-readalong/word-groups-v1/position.json')
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard

def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(code)
def opened():return xbmcgui.Window(10000).getProperty('AsterEpubReadAlong.Window')
def prop(name):return xbmc.getInfoLabel('Window.Property(EpubRead.'+name+')')
def press(action):
    require(action in ('left','right','down','select','back'),'epub-readalong-native-input')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in result,'epub-readalong-native-input-failed')
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def launch(pin):
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+pin+')')
    until(lambda:bool(opened()) and prop('State') in ('Ready','Resume ready','Complete','Progress cleared'),'epub-readalong-native-ready')
    require(focus(500),'epub-readalong-native-text-focus')
def close():
    press('back');until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000,'epub-readalong-native-close',20)

cp=None;original=None;result=dict(passed=False,checks_enforced=True,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==2 and guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not opened(),'epub-readalong-native-idle-home')
    pin=sys.argv[1];require(re.fullmatch('[a-f0-9]{64}',pin),'epub-readalong-native-pin')
    raw=(ROOT/'manifest.json').read_bytes();require(hashlib.sha256(raw).hexdigest()==pin,'epub-readalong-native-manifest')
    manifest=json.loads(raw);require(manifest['synthetic'] is True and manifest['word_timestamps'] is True
        and manifest['connected_phrase_cues'] is True,'epub-readalong-native-boundary')
    before=guard.snapshot();original=xbmcgui.Window(10000).getFocusId();cp=Path('/storage/.aster-checkpoints')/('aster-epub-readalong-native-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    require(not STATE.exists(),'epub-readalong-native-state-preexists')
    launch(pin);require(guard.idle() and prop('Active')=='-1' and prop('Sample')=='0','epub-readalong-native-no-autoplay')
    press('down');until(lambda:focus(201),'epub-readalong-native-play-focus')
    press('select');until(lambda:prop('State')=='Reading' and int(prop('Sample'))>0
                         and int(prop('Active'))>=0,'epub-readalong-native-start',20)
    first=int(prop('Sample'));first_active=int(prop('Active'));require(first_active>=0,'epub-readalong-native-word-active')
    until(lambda:int(prop('Active'))>first_active,'epub-readalong-native-word-advance',8)
    press('select');until(lambda:prop('State')=='Paused','epub-readalong-native-pause')
    paused=int(prop('Sample'));xbmc.sleep(600);require(abs(int(prop('Sample'))-paused)<2400,'epub-readalong-native-pause-clock')
    press('back');until(lambda:not opened() and guard.idle(),'epub-readalong-native-back-stop',20)
    saved=json.loads(STATE.read_text());require(saved['sample']>=first and not saved['complete'],'epub-readalong-native-saved-position')
    launch(pin);require(prop('State')=='Resume ready' and abs(int(prop('Sample'))-saved['sample'])<2,'epub-readalong-native-resume-ready')
    press('down');until(lambda:focus(201),'epub-readalong-native-resume-play-focus')
    press('select');until(lambda:prop('State')=='Reading' and int(prop('Sample'))>=saved['sample'],'epub-readalong-native-resume-play',20)
    until(lambda:int(prop('Active'))>=10,'epub-readalong-native-connected-phrase-progress',12)
    until(lambda:prop('State')=='Complete' and guard.idle(),'epub-readalong-native-natural-end',20)
    completed=json.loads(STATE.read_text());require(completed['complete'] and completed['sample']==manifest['audio_frames'],'epub-readalong-native-completion')
    # Clear is three controls right from Play: Stop, Restart, Clear.
    for _ in range(3):press('right')
    until(lambda:focus(204),'epub-readalong-native-clear-focus');press('select')
    until(lambda:prop('State')=='Progress cleared' and not STATE.exists(),'epub-readalong-native-cleared')
    close();require(guard.snapshot()==before and guard.idle(),'epub-readalong-native-preservation')
    cache=Path('/storage/.aster-cache/aster-epub-readalong')
    require(not cache.exists() or not list(cache.glob('session-*.wav')),'epub-readalong-native-cache-clean')
    result.update(passed=True,no_autoplay=True,pause_freezes_clock=True,back_stops_and_saves=True,
                  reopen_resumes=True,word_groups_advance=True,connected_phrase_progress=True,natural_completion=True,
                  explicit_progress_cleanup=True,session_cache_removed=True,settings_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if opened() and xbmcgui.getCurrentWindowId()==int(opened()):
        try:close()
        except Exception:result['cleanup_required']=True
    if original and not opened() and xbmcgui.getCurrentWindowId()==10000 and guard.idle():xbmc.executebuiltin('Control.SetFocus('+str(original)+')')
    if cp:
        path=cp/'native.json';path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
