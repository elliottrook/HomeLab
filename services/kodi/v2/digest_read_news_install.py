"""One exact HP News XML successor, private checkpoint and paired recovery."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from digest_news_install import atomic

TARGET = '.kodi/addons/skin.asterhome/1080i/custom_1111_digest.xml'
BEFORE = 'fca45b9ef09cbca624f05c5ac5c569a5b66363d2f94759137c80f10dbf1b547b'
READER = 'aster-digest-reader6'
READER_PIN = 'ffab164e7dccc950abf4020c238fd0381883d89579dc98f2daeb7cc628b3c9c2'
CHECKPOINT = '.aster-checkpoints/aster-digest-read-news1'
READER_FILES = {'default.py', 'resources/lib/digest_read_model.py',
    'resources/lib/digest_read_pages.py', 'resources/skins/Default/1080i/DigestReader.xml'}


def require(value, code):
    if not value: raise ValueError(code)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def unlinked(path):
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'read-news-linked-path')


def inspect(stage, storage, pin):
    stage, storage = Path(stage), Path(storage)
    unlinked(stage/'manifest.json')
    require(sha(stage/'manifest.json')==pin, 'read-news-manifest-pin')
    manifest = json.loads((stage/'manifest.json').read_text())
    require(manifest['kind']=='hp-digest-read-news.v1' and
        manifest['reader_manifest_sha256']==READER_PIN, 'read-news-contract')
    require(len(manifest['files'])==1 and manifest['files'][0]['path']==TARGET and
        manifest['files'][0]['before_sha256']==BEFORE, 'read-news-exact-target')
    require(set(manifest['helpers'])=={'digest_read_news_install.py','deploy_digest_read_news.py',
        'digest_news_install.py'}, 'read-news-exact-helpers')
    for name,digest in manifest['helpers'].items():
        unlinked(stage/name)
        require(sha(stage/name)==digest, 'read-news-helper-drift')
    payload = stage/'payload'/TARGET
    unlinked(payload); unlinked(storage/TARGET)
    require(sha(payload)==manifest['files'][0]['sha256'], 'read-news-payload-drift')
    ET.fromstring(payload.read_bytes())
    reader = storage/'.aster-staging'/READER
    unlinked(reader/'manifest.json')
    require(sha(reader/'manifest.json')==READER_PIN, 'read-news-reader-pin')
    members = json.loads((reader/'manifest.json').read_text())['files']
    require(len(members)==4 and {r['path'] for r in members}==READER_FILES, 'read-news-reader-members')
    for row in members:
        unlinked(reader/row['path'])
        require(sha(reader/row['path'])==row['sha256'], 'read-news-reader-drift')
    return manifest


def checkpoint(stage, storage, pin):
    manifest = inspect(stage,storage,pin)
    cp = Path(storage)/CHECKPOINT
    for name in ('manifest.json','original.xml','state.json'):
        unlinked(cp/name)
    require(sha(cp/'manifest.json')==pin and sha(cp/'original.xml')==BEFORE, 'read-news-recovery-drift')
    state = json.loads((cp/'state.json').read_text())['state']
    require(state in ('prepared','installed','rolled_back'), 'read-news-unknown-state')
    return manifest,state


def accepted_overrides(stage, storage, pin):
    manifest,state = checkpoint(stage,storage,pin)
    require(state!='prepared', 'read-news-recovery-required')
    digest = manifest['files'][0]['sha256'] if state=='installed' else BEFORE
    require(sha(Path(storage)/TARGET)==digest, 'read-news-installed-drift')
    return {TARGET:digest} if state=='installed' else {}


def run(mode, stage, storage, pin, *, idle):
    require(mode in ('install','verify','rollback'), 'read-news-mode')
    stage,storage = Path(stage),Path(storage)
    manifest = inspect(stage,storage,pin)
    require(idle(), 'read-news-home-idle-required')
    cp,target = storage/CHECKPOINT,storage/TARGET
    after = manifest['files'][0]['sha256']
    if mode=='verify':
        overrides = accepted_overrides(stage,storage,pin)
        return dict(verified=True, active=bool(overrides), files=1, reader_files=4)
    if mode=='rollback':
        _,state = checkpoint(stage,storage,pin)
        require(sha(target) in ((BEFORE,after) if state=='prepared' else
            ((after,) if state=='installed' else (BEFORE,))), 'read-news-rollback-drift')
        require(idle(), 'read-news-home-idle-required')
        atomic(target,(cp/'original.xml').read_bytes())
        require(sha(target)==BEFORE, 'read-news-restore-failed')
        atomic(cp/'state.json', b'{"state":"rolled_back"}\n')
        return dict(rolled_back=True, original_restored=True, staged_reader_retained=True)
    require(sha(target)==BEFORE, 'read-news-exact-predecessor')
    if cp.exists():
        _,state = checkpoint(stage,storage,pin)
        require(state=='rolled_back', 'read-news-checkpoint-state')
    else:
        unlinked(cp)
        cp.mkdir(parents=True,mode=0o700)
        atomic(cp/'manifest.json',(stage/'manifest.json').read_bytes())
        atomic(cp/'original.xml',target.read_bytes())
        require(sha(cp/'original.xml')==BEFORE, 'read-news-backup-not-verified')
        atomic(cp/'state.json',b'{"state":"prepared"}\n')
    require(idle() and sha(target)==BEFORE, 'read-news-source-changed')
    try:
        atomic(target,(stage/'payload'/TARGET).read_bytes())
        require(sha(target)==after, 'read-news-activation-failed')
        atomic(cp/'state.json',b'{"state":"installed"}\n')
        accepted_overrides(stage,storage,pin)
    except Exception:
        require(sha(target) in (BEFORE,after), 'read-news-unknown-recovery-state')
        atomic(target,(cp/'original.xml').read_bytes())
        atomic(cp/'state.json',b'{"state":"rolled_back"}\n')
        raise
    return dict(installed=True, files=1, reader_files=4, checkpoint_verified=True)
