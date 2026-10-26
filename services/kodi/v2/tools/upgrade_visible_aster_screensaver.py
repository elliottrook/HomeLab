"""HP-only visual refresh for the installed Aster idle saver."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
TARGET=Path('/storage/.kodi/addons/screensaver.asterhome.v2lab')
CHECKPOINTS=Path('/storage/.aster-checkpoints')
CHANGED=('idle_presentation.py','resources/skins/Default/1080i/AsterIdle.xml','resources/mark.png')
OLD={
 'idle_presentation.py':'278aefa8c1510629b4d87bbcdd88471878f4b81630ac435ef7fa7bf97f107fcc',
 'resources/skins/Default/1080i/AsterIdle.xml':'2b703d10cbc60fbc6ef2e7c726ab50c0abda92deb4d437100e566cc6342d4591',
 'resources/mark.png':'62f29492ac60b034df405d497817ac5e6ce7ce1ec536d946c63bed5659eb8ffd'}

def require(ok,code):
    if not ok:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,source):
    require(path.is_file() and not path.is_symlink() and source.is_file() and not source.is_symlink(),'idle-logo-file-boundary')
    fd,name=tempfile.mkstemp(prefix='.aster-idle-logo-',dir=str(path.parent))
    try:
        with os.fdopen(fd,'wb') as output:
            output.write(source.read_bytes());output.flush();os.fsync(output.fileno())
        os.chmod(name,0o600);os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
def candidate(pin):
    require(re.fullmatch('[a-f0-9]{64}',pin),'idle-logo-pin-shape')
    manifest=ROOT/'manifest.json';require(sha(manifest)==pin,'idle-logo-manifest-pin')
    value=json.loads(manifest.read_text())
    require(value['kind']=='hp-idle-presentation.v2' and value['addon_id']=='screensaver.asterhome.v2lab',
            'idle-logo-manifest-contract')
    rows={row['path']:row for row in value['files']}
    require(set(CHANGED)<=set(rows),'idle-logo-candidate-members')
    for name in CHANGED:
        source=ROOT/'payload/screensaver.asterhome.v2lab'/name
        require(source.stat().st_size==rows[name]['bytes'] and sha(source)==rows[name]['sha256'],'idle-logo-candidate-drift')
    return rows
def idle():
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}'))
    return ('error' not in reply and not reply.get('result') and xbmcgui.getCurrentWindowId()==10000 and
            xbmcgui.getCurrentWindowDialogId() in (-1,0,9999) and not xbmc.getCondVisibility('System.ScreenSaverActive') and
            not xbmcgui.Window(10000).getProperty('AsterIdle.Window'))

if __name__=='__main__':
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==2 and idle(),'idle-logo-hp-idle-home')
    rows=candidate(sys.argv[1]);current={name:sha(TARGET/name) for name in CHANGED}
    wanted={name:rows[name]['sha256'] for name in CHANGED}
    result=dict(kind='aster-visible-idle-logo.v1',passed=False,production_changed=False,before=current,after=wanted)
    if current==wanted:
        result.update(passed=True,already_current=True)
    else:
        require(current==OLD,'idle-logo-installed-drift')
        checkpoint=CHECKPOINTS/('aster-visible-idle-logo-'+str(time.time_ns()));checkpoint.mkdir(mode=0o700)
        for name in CHANGED:
            destination=checkpoint/name;destination.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
            shutil.copyfile(TARGET/name,destination);destination.chmod(0o600)
            require(sha(destination)==OLD[name],'idle-logo-checkpoint-drift')
        (checkpoint/'before.json').write_text(json.dumps(result,sort_keys=True)+'\n');(checkpoint/'before.json').chmod(0o600)
        try:
            require(idle(),'idle-logo-context-changed')
            for name in CHANGED:atomic(TARGET/name,ROOT/'payload/screensaver.asterhome.v2lab'/name)
            require(idle() and {name:sha(TARGET/name) for name in CHANGED}==wanted,'idle-logo-install-verification')
            result.update(passed=True,already_current=False,checkpoint=str(checkpoint),changed=list(CHANGED))
        except Exception:
            # Restore only the two files this operation owns and only from its
            # just-verified checkpoint. Never replace the add-on directory.
            for name in CHANGED:
                if sha(TARGET/name) in (OLD[name],wanted[name]):atomic(TARGET/name,checkpoint/name)
            require({name:sha(TARGET/name) for name in CHANGED}==OLD,'idle-logo-rollback-failed')
            raise
    report=ROOT/('upgrade-'+str(time.time_ns())+'.json')
    report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');report.chmod(0o600)
