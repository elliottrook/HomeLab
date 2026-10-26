"""Exact new HP add-on files and private checkpoint; never restores a live DB."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time

IDENTITY='screensaver.asterhome.v2lab'
TARGET='.kodi/addons/'+IDENTITY
CHECKPOINT='.aster-checkpoints/aster-idle-presentation2'
MEMBERS={'addon.xml','default.py','idle_presentation.py','resources/settings.xml',
    'resources/skins/Default/1080i/AsterIdle.xml','resources/mark.png','resources/solid.png'}
def require(ok,code):
    if not ok:raise ValueError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unlinked(path):
    require(not any(p.is_symlink() for p in (path,*path.parents)),'idle-linked-path')
def atomic(path,data):
    unlinked(path);fd,name=tempfile.mkstemp(prefix='.idle-',dir=str(path.parent))
    with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def inspect(stage,pin):
    stage=Path(stage);unlinked(stage/'manifest.json');require(sha(stage/'manifest.json')==pin,'idle-manifest-pin')
    m=json.loads((stage/'manifest.json').read_text())
    require(m['kind']=='hp-idle-presentation.v2' and m['addon_id']==IDENTITY and m['default_mode']=='black',
        'idle-manifest-contract')
    require(all(m[k] is False for k in ('normal_entry','network','speech','settings_changes')),'idle-boundaries')
    require(len(m['files'])==7 and {r['path'] for r in m['files']}==MEMBERS,'idle-exact-members')
    require(set(m['helpers'])=={'idle_screensaver_install.py','deploy_idle_screensaver.py'},'idle-exact-helpers')
    for name,digest in m['helpers'].items():
        unlinked(stage/name);require(sha(stage/name)==digest,'idle-helper-drift')
    require(m['archive']==IDENTITY+'-0.1.0.zip','idle-exact-archive')
    unlinked(stage/m['archive']);require(sha(stage/m['archive'])==m['archive_sha256'],'idle-archive-drift')
    for r in m['files']:
        p=stage/'payload'/IDENTITY/r['path'];unlinked(p)
        require(p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'idle-payload-drift')
    return m
def checkpoint(stage,storage,pin):
    m=inspect(stage,pin);cp=Path(storage)/CHECKPOINT
    for name in ('manifest.json','Addons33.db','baseline.json','state.json'):unlinked(cp/name)
    require(sha(cp/'manifest.json')==pin,'idle-checkpoint-pin')
    baseline=json.loads((cp/'baseline.json').read_text())
    require(sha(cp/'Addons33.db')==baseline['addon_database_sha256'],'idle-checkpoint-db-drift')
    state=json.loads((cp/'state.json').read_text())['state']
    require(state in ('prepared','installed','registered','disabled'),'idle-checkpoint-state')
    return m,baseline,state
def verify_files(stage,storage,pin):
    m,baseline,state=checkpoint(stage,storage,pin)
    target=Path(storage)/TARGET
    actual={str(p.relative_to(target)) for p in target.rglob('*') if p.is_file() and
        '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
    require(actual==MEMBERS,'idle-installed-file-set')
    for r in m['files']:
        p=target/r['path'];unlinked(p);require(sha(p)==r['sha256'],'idle-installed-drift')
    return m,baseline,state
def prepare(stage,storage,pin,baseline,*,idle):
    stage,storage=Path(stage),Path(storage);m=inspect(stage,pin)
    require(idle(),'idle-home-idle-required');target=storage/TARGET;cp=storage/CHECKPOINT
    unlinked(target);unlinked(cp)
    if cp.exists():
        _,original,state=verify_files(stage,storage,pin)
        require(state in ('installed','registered','disabled'),'idle-recovery-required')
        return original
    require(not target.exists() and IDENTITY not in baseline['inventory'],'idle-existing-addon-refused')
    source=storage/'.kodi/userdata/Database/Addons33.db';unlinked(source)
    require(source.is_file(),'idle-addon-database-missing')
    cp.mkdir(parents=True,mode=0o700)
    atomic(cp/'manifest.json',(stage/'manifest.json').read_bytes())
    database=cp/'Addons33.db'
    source_db=sqlite3.connect('file:'+str(source)+'?mode=ro',uri=True,timeout=2)
    restored=sqlite3.connect(database,timeout=2)
    deadline=time.monotonic()+5
    def progress(status,remaining,total):require(time.monotonic()<deadline,'idle-addon-backup-timeout')
    try:
        source_db.backup(restored,pages=128,progress=progress)
        require(restored.execute('PRAGMA integrity_check').fetchall()==[('ok',)],'idle-addon-database-integrity')
    finally:restored.close();source_db.close()
    database.chmod(0o600)
    baseline=dict(baseline,addon_database_sha256=sha(database))
    atomic(cp/'baseline.json',(json.dumps(baseline,sort_keys=True)+'\n').encode())
    atomic(cp/'state.json',b'{"state":"prepared"}\n')
    require(idle() and not target.exists(),'idle-install-state-changed')
    candidate=Path(tempfile.mkdtemp(prefix='.aster-idle-',dir=str(target.parent)))
    for r in m['files']:
        p=candidate/r['path'];p.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
        shutil.copyfile(stage/'payload'/IDENTITY/r['path'],p);p.chmod(0o600)
        require(sha(p)==r['sha256'],'idle-copy-drift')
    require(idle() and not target.exists(),'idle-install-state-changed')
    os.rename(candidate,target)
    atomic(cp/'state.json',b'{"state":"installed"}\n')
    verify_files(stage,storage,pin)
    return baseline
def mark(stage,storage,pin,state):
    require(state in ('registered','disabled'),'idle-state-target')
    verify_files(stage,storage,pin)
    atomic(Path(storage)/CHECKPOINT/'state.json',json.dumps(dict(state=state)).encode()+b'\n')
