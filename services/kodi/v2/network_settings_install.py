"""One exact HP Settings successor, pinned Network dependency and rollback."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from digest_news_install import atomic

TARGET='.kodi/addons/skin.asterhome/1080i/Settings.xml'
BEFORE='09a98be3b9ecddf185f61fdfb561bf9e68c4be123816e4f78ecc34210e136ab4'
NETWORK='aster-network-preview5'
NETWORK_PIN='73fd1e24fbb3b8f051c250beff1bcbaa018f88b265dabcc163a822bd367aa9d1'
CHECKPOINT='.aster-checkpoints/aster-network-settings3'
MEMBERS={'default.py','network_diagnostics.py','network_service_checks.py',
    'resources/skins/Default/1080i/NetworkPreview.xml','resources/skins/Default/1080i/DiagnosticsMenu.xml'}

def require(ok,code):
    if not ok:raise ValueError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def unlinked(path):
    require(not any(p.is_symlink() for p in (path,*path.parents)),'network-settings-linked')

def inspect(stage,storage,pin):
    stage,storage=Path(stage),Path(storage)
    unlinked(stage/'manifest.json');require(sha(stage/'manifest.json')==pin,'network-settings-pin')
    m=json.loads((stage/'manifest.json').read_text())
    require(m['kind']=='hp-network-settings.v1' and m['network_manifest_sha256']==NETWORK_PIN,
        'network-settings-contract')
    require(len(m['files'])==1 and m['files'][0]['path']==TARGET and
        m['files'][0]['before_sha256']==BEFORE,'network-settings-exact-target')
    require(set(m['helpers'])=={'network_settings_install.py','deploy_network_settings.py',
        'digest_news_install.py'},'network-settings-exact-helpers')
    for name,digest in m['helpers'].items():
        unlinked(stage/name);require(sha(stage/name)==digest,'network-settings-helper-drift')
    payload=stage/'payload'/TARGET;unlinked(payload);unlinked(storage/TARGET)
    require(sha(payload)==m['files'][0]['sha256'],'network-settings-payload-drift')
    ET.fromstring(payload.read_bytes())
    network=storage/'.aster-staging'/NETWORK
    unlinked(network/'manifest.json');require(sha(network/'manifest.json')==NETWORK_PIN,'network-settings-view-pin')
    rows=json.loads((network/'manifest.json').read_text())['files']
    require(len(rows)==5 and {r['path'] for r in rows}==MEMBERS,'network-settings-view-members')
    for r in rows:
        unlinked(network/r['path']);require(sha(network/r['path'])==r['sha256'],'network-settings-view-drift')
    return m

def checkpoint(stage,storage,pin):
    m=inspect(stage,storage,pin);cp=Path(storage)/CHECKPOINT
    for name in ('manifest.json','original.xml','state.json'):unlinked(cp/name)
    require(sha(cp/'manifest.json')==pin and sha(cp/'original.xml')==BEFORE,'network-settings-recovery-drift')
    state=json.loads((cp/'state.json').read_text())['state']
    require(state in ('prepared','installed','rolled_back'),'network-settings-state')
    return m,state

def accepted_overrides(stage,storage,pin):
    m,state=checkpoint(stage,storage,pin)
    require(state!='prepared','network-settings-recovery-required')
    digest=m['files'][0]['sha256'] if state=='installed' else BEFORE
    require(sha(Path(storage)/TARGET)==digest,'network-settings-installed-drift')
    return {TARGET:digest} if state=='installed' else {}

def run(mode,stage,storage,pin,*,idle):
    require(mode in ('install','verify','rollback'),'network-settings-mode')
    stage,storage=Path(stage),Path(storage);m=inspect(stage,storage,pin)
    require(idle(),'network-settings-home-idle-required')
    cp,target=storage/CHECKPOINT,storage/TARGET;after=m['files'][0]['sha256']
    if mode=='verify':return dict(verified=True,active=bool(accepted_overrides(stage,storage,pin)),files=1)
    if mode=='rollback':
        _,state=checkpoint(stage,storage,pin)
        require(sha(target) in ((BEFORE,after) if state=='prepared' else
            ((after,) if state=='installed' else (BEFORE,))),'network-settings-rollback-drift')
        require(idle(),'network-settings-home-idle-required')
        atomic(target,(cp/'original.xml').read_bytes());require(sha(target)==BEFORE,'network-settings-restore-failed')
        atomic(cp/'state.json',b'{"state":"rolled_back"}\n')
        return dict(rolled_back=True,original_restored=True)
    require(sha(target)==BEFORE,'network-settings-exact-predecessor')
    if cp.exists():
        _,state=checkpoint(stage,storage,pin);require(state=='rolled_back','network-settings-checkpoint-state')
    else:
        unlinked(cp);cp.mkdir(parents=True,mode=0o700)
        atomic(cp/'manifest.json',(stage/'manifest.json').read_bytes());atomic(cp/'original.xml',target.read_bytes())
        require(sha(cp/'original.xml')==BEFORE,'network-settings-backup-not-verified')
        atomic(cp/'state.json',b'{"state":"prepared"}\n')
    require(idle() and sha(target)==BEFORE,'network-settings-source-changed')
    try:
        atomic(target,(stage/'payload'/TARGET).read_bytes());require(sha(target)==after,'network-settings-activation-failed')
        atomic(cp/'state.json',b'{"state":"installed"}\n');accepted_overrides(stage,storage,pin)
    except Exception:
        require(sha(target) in (BEFORE,after),'network-settings-unknown-recovery-state')
        atomic(target,(cp/'original.xml').read_bytes());atomic(cp/'state.json',b'{"state":"rolled_back"}\n');raise
    return dict(installed=True,files=1,checkpoint_verified=True)
