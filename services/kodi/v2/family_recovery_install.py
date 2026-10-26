"""Adopt, verify, roll back or reinstall the consolidated HP family bundle."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


ADDON = Path('.kodi/addons/script.asterruntime')
SKIN = Path('.kodi/addons/skin.asterhome')
PLAYER = Path('.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/player.py')
CHECKPOINT = Path('.aster-checkpoints/aster-family-runtime7')


def require(value, code):
    if not value: raise ValueError(code)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, raw):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix='.aster-family7-',dir=path.parent)
    try:
        with os.fdopen(descriptor,'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name,0o644); os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)


def safe(value):
    path=Path(value)
    require(path.parts and not path.is_absolute() and '..' not in path.parts,
            'family7-relative-path')
    return path


def inspect(bundle,pin):
    bundle=Path(bundle)
    require(re.fullmatch('[0-9a-f]{64}',pin or '') and sha(bundle/'manifest.json')==pin,
            'family7-pin')
    value=json.loads((bundle/'manifest.json').read_text())
    require(value.get('kind')=='aster-family-recovery.v1'
            and len(value.get('skin',[]))==8 and len(value.get('external',[]))==1,
            'family7-contract')
    helpers=value.get('helpers',{})
    require(set(helpers)=={'family_recovery_install.py','deploy_family_recovery.py'}
            and all(sha(bundle/name)==expected for name,expected in helpers.items()),
            'family7-helper')
    for row in value['addon_files']:
        relative=safe(row['path']); path=bundle/'script.asterruntime'/relative
        require(path.is_file() and not path.is_symlink() and path.stat().st_size==row['bytes']
                and sha(path)==row['sha256'],'family7-addon-payload')
    for row in value['skin']:
        relative=safe(row['path'])
        require(sha(bundle/'skin'/relative)==row['sha256']
                and sha(bundle/'original'/relative)==row['before_sha256'],
                'family7-skin-payload')
    row=value['external'][0]; require(safe(row['path'])==PLAYER,'family7-player-target')
    require(sha(bundle/'external/player.py')==row['sha256']
            and sha(bundle/'external/player.py.before')==row['before_sha256'],
            'family7-player-payload')
    return value


def verify_addon(root,rows):
    root=Path(root); require(root.is_dir() and not root.is_symlink(),'family7-addon-missing')
    expected={r['path']:r for r in rows}
    for relative,row in expected.items():
        path=root/relative
        require(path.is_file() and not path.is_symlink() and path.stat().st_size==row['bytes']
                and sha(path)==row['sha256'],'family7-addon-drift')
    for path in root.rglob('*'):
        if path.is_dir() and not path.is_symlink(): continue
        relative=path.relative_to(root).as_posix()
        require(relative in expected or (path.is_file() and not path.is_symlink()
                and (path.name=='entry.lock' or ('__pycache__' in path.parts and path.suffix=='.pyc'))),
                'family7-addon-extra')


def verify_state(storage,value,active):
    storage=Path(storage); addon=storage/ADDON
    if active: verify_addon(addon,value['addon_files'])
    else: require(not addon.exists(),'family7-baseline-addon-present')
    for row in value['skin']:
        require(sha(storage/SKIN/row['path'])==(row['sha256'] if active else row['before_sha256']),
                'family7-skin-drift')
    row=value['external'][0]
    require(sha(storage/PLAYER)==(row['sha256'] if active else row['before_sha256']),
            'family7-player-drift')


def prepare_checkpoint(bundle,storage,value,pin,state):
    bundle,storage=Path(bundle),Path(storage); checkpoint=storage/CHECKPOINT
    require(not checkpoint.exists(),'family7-checkpoint-exists')
    checkpoint.mkdir(parents=True,mode=0o700)
    atomic(checkpoint/'manifest.json',(bundle/'manifest.json').read_bytes())
    for row in value['skin']:
        atomic(checkpoint/'original'/row['path'],(bundle/'original'/row['path']).read_bytes())
    atomic(checkpoint/'player.py.before',(bundle/'external/player.py.before').read_bytes())
    atomic(checkpoint/'state.json',json.dumps({'state':state,'pin':pin},sort_keys=True).encode()+b'\n')
    return checkpoint


def checkpoint_state(storage,pin):
    checkpoint=Path(storage)/CHECKPOINT
    require(sha(checkpoint/'manifest.json')==pin,'family7-checkpoint-manifest')
    state=json.loads((checkpoint/'state.json').read_text())
    require(state.get('pin')==pin and state.get('state') in ('installed','rolled_back'),
            'family7-checkpoint-state')
    return checkpoint,state['state']


def run(mode,bundle,storage,pin,*,idle):
    require(mode in ('adopt','verify','rollback','install'),'family7-mode')
    bundle,storage=Path(bundle),Path(storage); value=inspect(bundle,pin)
    require(idle(),'family7-home-idle-required')
    checkpoint=storage/CHECKPOINT
    if mode=='adopt':
        verify_state(storage,value,True)
        prepare_checkpoint(bundle,storage,value,pin,'installed')
        return dict(adopted=True,files_verified=len(value['addon_files'])+len(value['skin'])+1)
    checkpoint,state=checkpoint_state(storage,pin)
    if mode=='verify':
        verify_state(storage,value,state=='installed')
        return dict(verified=True,active=state=='installed')
    if mode=='rollback':
        require(state=='installed','family7-not-active'); verify_state(storage,value,True)
        retired=checkpoint/'retired-runtime'; require(not retired.exists(),'family7-retired-exists')
        os.rename(storage/ADDON,retired)
        for row in value['skin']:
            atomic(storage/SKIN/row['path'],(checkpoint/'original'/row['path']).read_bytes())
        atomic(storage/PLAYER,(checkpoint/'player.py.before').read_bytes())
        atomic(checkpoint/'state.json',json.dumps({'state':'rolled_back','pin':pin},sort_keys=True).encode()+b'\n')
        verify_state(storage,value,False)
        return dict(rolled_back=True,recovery_retained=True)
    require(state=='rolled_back','family7-install-state'); verify_state(storage,value,False)
    temporary=(storage/ADDON).with_name('script.asterruntime.installing7')
    require(not temporary.exists(),'family7-temporary-exists')
    temporary.mkdir(parents=True,mode=0o700)
    for row in value['addon_files']:
        atomic(temporary/row['path'],(bundle/'script.asterruntime'/row['path']).read_bytes())
    verify_addon(temporary,value['addon_files']); os.rename(temporary,storage/ADDON)
    for row in value['skin']:
        atomic(storage/SKIN/row['path'],(bundle/'skin'/row['path']).read_bytes())
    atomic(storage/PLAYER,(bundle/'external/player.py').read_bytes())
    atomic(checkpoint/'state.json',json.dumps({'state':'installed','pin':pin},sort_keys=True).encode()+b'\n')
    verify_state(storage,value,True)
    return dict(installed=True,files_verified=len(value['addon_files'])+len(value['skin'])+1)

