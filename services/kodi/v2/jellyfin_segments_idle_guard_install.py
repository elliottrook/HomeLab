"""Install or roll back the hash-pinned HP Jellyfin segment checker guard."""
import hashlib,json,os,re,tempfile
from pathlib import Path

TARGET=Path('.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/segments.py')
CHECKPOINT=Path('.aster-checkpoints/aster-jellyfin-segments-guard-20261026')
def require(value,code):
    if not value: raise ValueError(code)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic(path,raw):
    path=Path(path); descriptor,name=tempfile.mkstemp(prefix='.segments-guard-',dir=path.parent)
    try:
        with os.fdopen(descriptor,'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name,0o644); os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)
def kodi_running():
    for path in Path('/proc').glob('[0-9]*'):
        try:
            if (path/'comm').read_text().strip()=='kodi.bin': return True
        except OSError: pass
    return False
def inspect(stage,pin):
    stage=Path(stage); require(re.fullmatch('[0-9a-f]{64}',pin or '') and sha(stage/'manifest.json')==pin,'segments-guard-pin')
    value=json.loads((stage/'manifest.json').read_text())
    require(value.get('kind')=='hp-jellyfin-segments-idle-guard.v1' and value.get('target')==str(TARGET),'segments-guard-contract')
    require(sha(stage/'segments.py')==value.get('sha256') and (stage/'segments.py').stat().st_size==value.get('bytes'),'segments-guard-payload')
    return value
def run(mode,stage,storage,pin):
    require(mode in ('install','verify','rollback'),'segments-guard-mode')
    stage,storage=Path(stage),Path(storage); value=inspect(stage,pin); target=storage/TARGET; checkpoint=storage/CHECKPOINT
    if mode=='verify':
        require(sha(target)==value['sha256'],'segments-guard-not-active'); return dict(verified=True,active=True)
    require(not kodi_running(),'segments-guard-stop-kodi-first')
    if mode=='rollback':
        require(sha(target)==value['sha256'] and json.loads((checkpoint/'state.json').read_text()).get('state')=='installed','segments-guard-rollback-drift')
        atomic(target,(checkpoint/'segments.py.before').read_bytes()); require(sha(target)==value['before_sha256'],'segments-guard-rollback-failed')
        atomic(checkpoint/'state.json',b'{"state":"rolled_back"}\n'); return dict(rolled_back=True,recovery_retained=True)
    require(sha(target)==value['before_sha256'] and not checkpoint.exists(),'segments-guard-live-drift')
    checkpoint.mkdir(parents=True,mode=0o700); atomic(checkpoint/'segments.py.before',target.read_bytes()); atomic(checkpoint/'manifest.json',(stage/'manifest.json').read_bytes()); atomic(checkpoint/'state.json',b'{"state":"prepared"}\n')
    try:
        atomic(target,(stage/'segments.py').read_bytes()); require(sha(target)==value['sha256'],'segments-guard-install-failed'); atomic(checkpoint/'state.json',b'{"state":"installed"}\n')
    except Exception:
        if sha(target)==value['sha256']: atomic(target,(checkpoint/'segments.py.before').read_bytes())
        atomic(checkpoint/'state.json',b'{"state":"rolled_back"}\n'); raise
    return dict(installed=True,checkpoint_verified=True)

