"""Native idle-only HP News install/verify/rollback, no service/settings writes."""
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmcgui

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from digest_news_install import run, inspect, CHECKPOINT, PLAYER

if __name__ == '__main__':
    def require(value, code):
        if not value: raise ValueError(code)
    require(os.uname().nodename == 'AsterTV' and len(sys.argv) in (3, 4), 'hp-news-arguments')
    mode, pin = sys.argv[1:3]
    require(re.fullmatch('[0-9a-f]{64}', pin), 'news-pin-format')
    inspect(ROOT, Path('/storage'), pin)
    sys.path.insert(0, '/storage/.aster-staging/'+PLAYER+'/resources/lib')
    import deploy_startup as guard
    lock = os.open(str(ROOT/'deploy.lock'), os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        before = guard.snapshot()
        idle = lambda:guard.idle() and xbmcgui.getCurrentWindowId() == 10000
        if mode == 'install':
            require(len(sys.argv) == 4 and re.fullmatch(r'postcheck-[0-9]+\.json', sys.argv[3]), 'fresh-news-preflight-required')
            proof = json.loads((Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/sys.argv[3]).read_text())
            require(-10 <= time.time()-int(sys.argv[3][10:-5])/1e9 <= 120, 'news-preflight-age')
            require(all(proof.get(key) is True for key in ('checks_enforced', 'no_player', 'original_empty_queue',
                'all_lab_windows_closed', 'music_shuffle_off')) and proof.get('av_language_settings_verified') == 68,
                'news-preflight-contract')
        result = run(mode, ROOT, Path('/storage'), pin, idle=idle)
        require(before == guard.snapshot(), 'news-settings-navigation-changed')
        result.update(settings_navigation_unchanged=True, idle_empty=guard.idle())
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        code = str(error)
        result = dict(passed=False, code=code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__)
    finally: os.close(lock)
    (ROOT/('result-'+str(time.time_ns())+'.json')).write_text(json.dumps(result, indent=2))
