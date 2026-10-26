"""Private HP/Frigate one-camera setup, exact actor/paths, public-key-only output."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

HOSTKEY=b'192.168.20.10 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF4bgh0A2kkhcxtGD8muykvCcDp+uM/7ckYsUfXm4D7b\n'
OWNER_SHA='b6fcf8ceba62720f6be6092e49c6b38211b5564e70bb15be0172c4432533b1fa'
def require(ok,code):
    if not ok:raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'camera-install-file')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,raw):
    require(not path.parent.is_symlink() and not path.is_symlink(),'camera-install-symlink')
    fd,tmp=tempfile.mkstemp(prefix='.camera-install.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def restricted_line(public):
    parts=public.split();require(len(parts)==2 and parts[0]=='ssh-ed25519' and re.fullmatch('[A-Za-z0-9+/=]{68}',parts[1]),'camera-install-public-key')
    raw=base64.b64decode(parts[1],validate=True);require(len(raw)==51 and raw[:19]==b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20','camera-install-key-type')
    return ('restrict,from="192.168.1.140",command="/usr/bin/python3 /home/jelliott/.aster-camera-source/frame.py" '+public+' aster-hp-camera-v1\n').encode()
def keys_changed(raw,line,enable):
    require(raw.endswith(b'\n'),'camera-install-key-newline')
    key=line.split(b' ssh-ed25519 ')[1].split()[0]
    matches=[r for r in raw.splitlines(keepends=True) if key in r or b'aster-hp-camera-v1' in r]
    require(not matches or matches==[line],'camera-install-key-drift')
    return (raw if matches else raw+line) if enable else raw.replace(line,b'')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('actor',choices=('hp','frigate'));parser.add_argument('mode',choices=('prepare','verify','enable-key','disable-key'))
    parser.add_argument('pin');parser.add_argument('--public-key',default='');args=parser.parse_args()
    stage=Path(__file__).resolve().parent
    require(re.fullmatch('aster-camera[0-9]+',stage.name),'camera-install-stage')
    hp=args.actor=='hp'
    require(not hp or args.mode in ('prepare','verify'),'camera-install-hp-mode')
    require((hp and os.uname().nodename=='AsterTV' and os.getuid()==0 and stage.parent==Path('/storage/.aster-staging')) or
            (not hp and os.uname().nodename=='frigate' and Path.home()==Path('/home/jelliott') and stage.parent==Path('/home/jelliott/.aster-camera-staging')),'camera-install-actor')
    require(digest(stage/'manifest.json')==args.pin,'camera-install-manifest')
    raw=(stage/'manifest.json').read_bytes();manifest=json.loads(raw);files=manifest['files']
    require(manifest['kind']=='hp-one-camera-v1' and set(files)=={'frame.py','proxy.py','view.py','aster-camera.service','camera-idle.png','custom_1112_home.xml'},'camera-install-payload')
    for name,pin in files.items():require(digest(stage/name)==pin,'camera-install-stage-drift')
    root=Path('/storage/.aster-camera') if hp else Path('/home/jelliott/.aster-camera-source')
    cp=(Path('/storage/.aster-checkpoints') if hp else Path('/home/jelliott/.aster-camera-checkpoints'))/stage.name
    members=('proxy.py','view.py','camera-idle.png') if hp else ('frame.py',)
    keys=Path('/home/jelliott/.ssh/authorized_keys')
    unit=Path('/storage/.config/system.d/aster-camera.service')
    target=Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1112_home.xml')
    if args.mode=='prepare':
        require(not root.exists() and not cp.exists(),'camera-install-already-prepared')
        if hp:require(not unit.exists() and digest(target)==manifest['predecessor'],'camera-install-hp-predecessor')
        else:require(digest(keys)==OWNER_SHA and keys.stat().st_mode&0o777==0o600,'camera-install-owner-drift')
        cp.mkdir(mode=0o700,parents=True);root.mkdir(mode=0o700)
        atomic(cp/'manifest.json',raw)
        if hp:
            atomic(cp/'custom_1112_home.xml',target.read_bytes())
            atomic(unit,(stage/'aster-camera.service').read_bytes())
            atomic(root/'known_hosts',HOSTKEY)
            subprocess.run(['/usr/bin/ssh-keygen','-q','-t','ed25519','-N','','-C','aster-hp-camera-v1','-f',str(root/'id_ed25519')],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
        else:
            line=restricted_line(args.public_key);keys_changed(keys.read_bytes(),line,True)
            atomic(cp/'authorized_keys.before',keys.read_bytes());atomic(cp/'restricted-key.line',line)
        for name in members:atomic(root/name,(stage/name).read_bytes())
        with tempfile.TemporaryDirectory(prefix='restore-',dir=cp) as folder:
            name='custom_1112_home.xml' if hp else 'authorized_keys.before'
            restored=Path(folder)/name;restored.write_bytes((cp/name).read_bytes())
            require(digest(restored)==digest(cp/name),'camera-install-isolated-restore')
    require(not root.is_symlink() and not cp.is_symlink() and digest(cp/'manifest.json')==args.pin,'camera-install-checkpoint')
    for name in members:require(digest(root/name)==files[name],'camera-install-installed-drift')
    result=dict(passed=True,actor=args.actor,mode=args.mode,checkpoint_verified=True,isolated_restore_verified=True)
    if hp:
        require(digest(cp/'custom_1112_home.xml')==manifest['predecessor'] and digest(unit)==files['aster-camera.service'] and (root/'known_hosts').read_bytes()==HOSTKEY,'camera-install-hp-runtime-drift')
        info=(root/'id_ed25519').lstat();require(not (root/'id_ed25519').is_symlink() and info.st_mode&0o777==0o600 and info.st_nlink==1,'camera-install-private-key-mode')
        result['public_key']=' '.join((root/'id_ed25519.pub').read_text().split()[:2])
        result['private_key_exported']=False
    else:
        line=restricted_line(args.public_key);require((cp/'restricted-key.line').read_bytes()==line and digest(cp/'authorized_keys.before')==OWNER_SHA,'camera-install-source-checkpoint')
        before=keys.read_bytes();require(all(r in before.splitlines(keepends=True) for r in (cp/'authorized_keys.before').read_bytes().splitlines(keepends=True)),'camera-install-owner-key-removed')
        if args.mode in ('enable-key','disable-key'):atomic(keys,keys_changed(before,line,args.mode=='enable-key'))
        require(keys_changed(before,line,False)==keys_changed(keys.read_bytes(),line,False),'camera-install-other-key-change')
        result.update(key_enabled=line in keys.read_bytes().splitlines(keepends=True),owner_keys_preserved=True)
    atomic(cp/'state.json',json.dumps(result,sort_keys=True).encode());print(json.dumps(result))

if __name__=='__main__':main()
