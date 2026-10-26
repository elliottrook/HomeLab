"""HP machine-key restriction and exact receiver files; never a daemon or shell."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT=Path('/storage/.aster-home-delivery')
CP=Path('/storage/.aster-checkpoints/aster-home-delivery1')
KEYS=Path('/storage/.ssh/authorized_keys')
ORIGINAL='63fe0f9e709419fc801b3effdb5dfd94cdcd6665d7b0547c0b46a8e4c0c1f1b2'

def require(ok,code):
    if not ok:raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'delivery-install-file')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    require(not path.parent.is_symlink() and not path.is_symlink(),'delivery-install-symlink')
    fd,tmp=tempfile.mkstemp(prefix='.delivery-install.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def key_line(public):
    parts=public.split()
    require(len(parts)==2 and parts[0]=='ssh-ed25519' and re.fullmatch('[A-Za-z0-9+/=]{68}',parts[1]),'delivery-install-key-format')
    decoded=base64.b64decode(parts[1],validate=True)
    require(len(decoded)==51 and decoded[:19]==b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20','delivery-install-key-type')
    return ('restrict,from="192.168.20.11",command="/usr/bin/python3 /storage/.aster-home-delivery/receive.py" '
            +public+' aster-home-feed-v1\n').encode()

def transform(raw,line,enable):
    require(raw.endswith(b'\n'),'delivery-install-owner-key-newline')
    key=line.split(b' ssh-ed25519 ')[1].split()[0]
    matches=[r for r in raw.splitlines(keepends=True) if key in r or b'aster-home-feed-v1' in r]
    require(not matches or matches==[line],'delivery-install-duplicate-or-unrestricted-key')
    if enable:return raw if matches else raw+line
    return raw.replace(line,b'') if matches else raw

def run(mode,stage,pin,public):
    require(mode in ('prepare','enable','disable','verify'),'delivery-install-mode')
    require(digest(stage/'manifest.json')==pin,'delivery-install-manifest')
    manifest=json.loads((stage/'manifest.json').read_text());members=manifest['files']
    require(manifest['kind']=='hp-home-delivery-v1' and set(members)=={'receive.py','home_status_model.py'},'delivery-install-members')
    for name,wanted in members.items():require(digest(stage/name)==wanted,'delivery-install-stage')
    line=key_line(public)
    if mode=='prepare':
        require(not ROOT.exists() and not CP.exists(),'delivery-install-already-prepared')
        require(digest(KEYS)==ORIGINAL and KEYS.stat().st_mode&0o777==0o600,'delivery-install-owner-key-drift')
        before=KEYS.read_bytes();transform(before,line,True)
        CP.mkdir(mode=0o700);atomic(CP/'authorized_keys.before',before);atomic(CP/'manifest.json',(stage/'manifest.json').read_bytes())
        atomic(CP/'restricted-key.line',line)
        with tempfile.TemporaryDirectory(prefix='restore-',dir=CP) as folder:
            restored=Path(folder)/'authorized_keys';restored.write_bytes((CP/'authorized_keys.before').read_bytes())
            require(digest(restored)==ORIGINAL,'delivery-install-isolated-restore')
        ROOT.mkdir(mode=0o700)
        for name in members:atomic(ROOT/name,(stage/name).read_bytes())
    require(not ROOT.is_symlink() and not CP.is_symlink() and digest(CP/'manifest.json')==pin and
            digest(CP/'authorized_keys.before')==ORIGINAL and (CP/'restricted-key.line').read_bytes()==line,'delivery-install-checkpoint')
    for name,wanted in members.items():require(digest(ROOT/name)==wanted,'delivery-install-installed')
    current=KEYS.read_bytes();before=(CP/'authorized_keys.before').read_bytes()
    require(all(row in current.splitlines(keepends=True) for row in before.splitlines(keepends=True)),'delivery-install-owner-key-removed')
    if mode in ('enable','disable'):atomic(KEYS,transform(current,line,mode=='enable'))
    after=KEYS.read_bytes()
    require(transform(current,line,False)==transform(after,line,False),'delivery-install-other-keys-changed')
    result=dict(passed=True,mode=mode,restricted_key_enabled=line in after.splitlines(keepends=True),
                files_verified=2,owner_keys_preserved=True,checkpoint_verified=True,isolated_restore_verified=True)
    atomic(CP/'state.json',json.dumps(result,sort_keys=True).encode())
    return result
