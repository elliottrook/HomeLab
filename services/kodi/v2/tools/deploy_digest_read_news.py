"""Pinned HP Home/idle-only one-file News reading activation and rollback."""
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
from digest_read_news_install import run,inspect


if __name__=='__main__':
    def require(value,code):
        if not value: raise ValueError(code)
    require(os.uname().nodename=='AsterTV' and len(sys.argv) in (3,4),'read-news-hp-arguments')
    mode,pin=sys.argv[1:3]
    require(re.fullmatch('[0-9a-f]{64}',pin),'read-news-pin-format')
    inspect(ROOT,Path('/storage'),pin)
    sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
    import deploy_startup as guard
    lock=os.open(str(ROOT/'deploy.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        idle=lambda:guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not xbmcgui.Window(10000).getProperty('AsterDigest.ReaderWindow')
        before=guard.snapshot()
        if mode=='install':
            require(len(sys.argv)==4 and re.fullmatch(r'postcheck-[0-9]+\.json',sys.argv[3]),'read-news-fresh-preflight-required')
            require(-10<=time.time()-int(sys.argv[3][10:-5])/1e9<=120,'read-news-preflight-age')
            proof=json.loads((Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/sys.argv[3]).read_text())
            require(all(proof.get(k) is True for k in ('checks_enforced','no_player','original_empty_queue',
                'all_lab_windows_closed','music_shuffle_off')) and proof.get('av_language_settings_verified')==68,'read-news-preflight-contract')
        result=run(mode,ROOT,Path('/storage'),pin,idle=idle)
        if mode in ('install','rollback'):
            xbmc.executebuiltin('ReloadSkin')
            xbmc.sleep(1500)
        require(idle() and guard.snapshot()==before,'read-news-preservation')
        result.update(settings_navigation_unchanged=True,idle_empty=True)
    except (OSError,ValueError,KeyError,RuntimeError) as error:
        code=str(error)
        result=dict(passed=False,code=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__)
    finally:os.close(lock)
    (ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result,indent=2))
