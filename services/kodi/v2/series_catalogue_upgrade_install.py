"""Exact reversible installer for the HP series catalogue successor."""
import hashlib,json,os,re,shutil,tempfile
from pathlib import Path

CHECKPOINT=Path('.aster-checkpoints/aster-series-catalogue1')
ADDON=Path('.kodi/addons/script.asterruntime')
SKIN=Path('.kodi/addons/skin.asterhome')

def require(value,code):
    if not value:raise ValueError(code)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.series-catalogue.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(name,0o600);os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def inspect(stage,pin):
    stage=Path(stage);require(re.fullmatch('[0-9a-f]{64}',pin or '') and sha(stage/'manifest.json')==pin,
        'catalogue-upgrade-manifest-pin')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('kind')=='hp-series-catalogue-upgrade.v1'
        and manifest.get('component')=='aster-series-preview24'
        and manifest.get('component_files')==8,'catalogue-upgrade-contract')
    require(set(manifest.get('helpers',{}))=={'series_catalogue_upgrade_install.py','deploy_series_catalogue.py'},
        'catalogue-upgrade-helpers')
    for name,expected in manifest['helpers'].items():require(sha(stage/name)==expected,'catalogue-upgrade-helper-drift')
    component=stage/'component';candidate=json.loads((component/'manifest.json').read_text())
    require(sha(component/'manifest.json')==manifest['component_manifest_sha256']
        and len(candidate.get('files',[]))==8,'catalogue-upgrade-component')
    for row in candidate['files']:
        path=component/row['path'];require(path.is_file() and not path.is_symlink()
            and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'catalogue-upgrade-component-drift')
    require(len(manifest.get('replacements',[]))==4,'catalogue-upgrade-replacement-shape')
    for row in manifest['replacements']:
        path=stage/'replacements'/row['path'];require(path.is_file() and not path.is_symlink()
            and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'catalogue-upgrade-replacement-drift')
    return manifest

def target(storage,relative):
    relative=Path(relative)
    return Path(storage)/(SKIN/Path(*relative.parts[1:]) if relative.parts[0]=='skin'
        else ADDON/Path(*relative.parts[1:]))

def run(stage,storage,pin,*,idle):
    stage,storage=Path(stage),Path(storage);manifest=inspect(stage,pin)
    require(idle(),'catalogue-upgrade-home-idle-required')
    active=storage/ADDON/'aster-series-preview24';checkpoint=storage/CHECKPOINT
    require(active.is_dir() and sha(active/'manifest.json')==manifest['before_component_manifest_sha256'],
        'catalogue-upgrade-predecessor')
    for row in manifest['replacements']:
        require(sha(target(storage,row['path']))==row['before_sha256'],'catalogue-upgrade-live-drift')
    require(not checkpoint.exists(),'catalogue-upgrade-checkpoint-exists')
    checkpoint.mkdir(parents=True,mode=0o700)
    shutil.copytree(active,checkpoint/'original-series',symlinks=False)
    for row in manifest['replacements']:
        original=checkpoint/'original'/row['path'];original.parent.mkdir(parents=True,exist_ok=True)
        original.write_bytes(target(storage,row['path']).read_bytes());original.chmod(0o600)
    atomic(checkpoint/'manifest.json',(stage/'manifest.json').read_bytes())
    atomic(checkpoint/'state.json',b'{"state":"prepared"}\n')
    temporary=active.with_name(active.name+'.catalogue-installing')
    try:
        shutil.copytree(stage/'component',temporary)
        os.rename(active,checkpoint/'retired-series')
        os.rename(temporary,active)
        for row in manifest['replacements']:
            atomic(target(storage,row['path']),(stage/'replacements'/row['path']).read_bytes())
        require(sha(active/'manifest.json')==manifest['component_manifest_sha256'],'catalogue-upgrade-active-component')
        require(all(sha(target(storage,row['path']))==row['sha256'] for row in manifest['replacements']),
            'catalogue-upgrade-active-replacements')
        atomic(checkpoint/'state.json',b'{"state":"installed"}\n')
    except Exception:
        if temporary.exists():shutil.rmtree(temporary)
        if active.exists():shutil.rmtree(active)
        os.rename(checkpoint/'retired-series',active)
        for row in manifest['replacements']:
            atomic(target(storage,row['path']),(checkpoint/'original'/row['path']).read_bytes())
        atomic(checkpoint/'state.json',b'{"state":"rolled_back"}\n')
        raise
    return dict(installed=True,component_files=8,
                replacements=len(manifest['replacements']),checkpoint_verified=True)
