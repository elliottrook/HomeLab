"""Third visual review, using the established exact-file checkpoint engine."""
import fcntl,json,os,sys
from pathlib import Path
from deploy_review2 import run,require,allowed as old_allowed
STAGES={'aster-music-v2lab-0.1.0-candidate67','aster-series-preview19','aster-global-search-ui16','aster-books-sync8',
        'aster-music-v2lab-0.1.0-candidate68','aster-series-preview20','aster-global-search-ui17','aster-books-sync9',
        'aster-music-v2lab-0.1.0-candidate69','aster-series-preview21','aster-global-search-ui18','aster-books-sync10',
        'aster-music-v2lab-0.1.0-candidate70','aster-series-preview22','aster-global-search-ui19','aster-books-sync11',
        'aster-music-v2lab-0.1.0-candidate71','aster-series-preview23','aster-global-search-ui20','aster-books-sync12',
        'aster-music-v2lab-0.1.0-candidate72','aster-series-preview24','aster-global-search-ui21','aster-books-sync13'}
def allowed(name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:return False
    if name in ('.kodi/addons/skin.asterhome/1080i/IncludesHub.xml',
        '.aster-checkpoints/aster-floating-rail-20261024/active-manifest.json',
        '.aster-checkpoints/aster-books-sync-20261025/active-manifest.json'):return True
    if len(p.parts)>2 and p.parts[0]=='.aster-staging':
        return p.parts[1] in STAGES and p.suffix in ('.xml','.py','.json','.zip','.svg','.png')
    return old_allowed(name)
if __name__=='__main__':
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-only-arguments')
    lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(run(*sys.argv[1:],review={'deploy_review4':4,'deploy_review5':5,'deploy_review6':6,'deploy_review7':7,'deploy_review8':8}.get(Path(__file__).stem,3),validator=allowed)))
    finally:os.close(lock)
