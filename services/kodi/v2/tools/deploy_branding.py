"""Exact-file HP branding successor; use the existing private recovery engine."""
import fcntl,json,os,sys
from pathlib import Path
from deploy_review2 import run,require,allowed as prior
def allowed(name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:return False
    if name.startswith('.aster-staging/aster-global-search-ui22/'):
        return p.suffix in ('.py','.xml','.json')
    if name=='.kodi/addons/skin.asterhome/tools/header_search.py':return True
    return prior(name)
if __name__=='__main__':
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-only-arguments')
    lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(run(*sys.argv[1:],review=10 if Path(__file__).stem=='deploy_branding10' else 9,validator=allowed)))
    finally:os.close(lock)
