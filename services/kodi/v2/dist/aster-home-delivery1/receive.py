"""Forced-command, single-file display receiver. Standard library only.

No shell evaluation, network calls, Kodi/player APIs, arbitrary paths or
credential reads. Remote callers cannot choose a target or implementation.
"""
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import sys
import tempfile

ROOT=Path('/storage/.aster-home-delivery')
STAGE=Path('/storage/.aster-staging/aster-home-status1')
CP=Path('/storage/.aster-checkpoints/aster-home-status1')
FEED=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home-dashboard.json')
MANIFEST='4d125fe1ca9ad5d1fba34116a817766823dc98b4db97579a61a2016ce6a85be1'
COMMAND='aster-home-publish-v1'
SOURCE='192.168.20.11'

def require(ok,code):
    if not ok:raise RuntimeError(code)
def secure(path,directory=False):
    info=path.lstat()
    require(not path.is_symlink() and info.st_uid==os.getuid() and
            (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1) and
            not info.st_mode&0o022,'feed-receiver-private-path')
    return info
def digest(path):
    secure(path);return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,raw):
    secure(path.parent,True)
    if path.exists():secure(path)
    descriptor,tmp=tempfile.mkstemp(prefix='.delivery.',dir=path.parent)
    try:
        with os.fdopen(descriptor,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
        descriptor=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(descriptor)
        finally:os.close(descriptor)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def write_json(path,value):atomic(path,(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode())

def receive(raw,model,*,now=None,feed=FEED,checkpoint=CP,stage=STAGE):
    """Caller holds the same lock as the operator publisher. Params aid tests only."""
    now=now or datetime.now(timezone.utc)
    require(model.view(raw,now).state=='fresh','feed-receiver-invalid-or-stale')
    payload=json.loads(raw);stamp=model.validate(payload)
    pin=hashlib.sha256(raw).hexdigest()
    publication=checkpoint/'publication.json';pending=checkpoint/'delivery-pending.json'
    secure(feed.parent,True);secure(checkpoint,True)
    accepted=json.loads(publication.read_text())
    require(set(accepted)=={'feed_sha256','manifest_sha256'} and accepted['manifest_sha256']==MANIFEST,'feed-receiver-publication')
    actual=digest(feed)
    # Recover our own exact interrupted transition, never arbitrary user state.
    if pending.exists():
        secure(pending);transition=json.loads(pending.read_text())
        require(set(transition)=={'before','after','source_at','status'} and transition['status'] in ('pending','accepted'),'feed-receiver-journal')
        if transition['status']=='pending':
            require(actual in (transition['before'],transition['after']) and accepted['feed_sha256'] in (transition['before'],transition['after']),'feed-receiver-uncertain-write')
            if actual==transition['after']:
                accepted['feed_sha256']=actual;write_json(publication,accepted)
            else:require(accepted['feed_sha256']==actual,'feed-receiver-uncertain-write')
            transition['status']='accepted';write_json(pending,transition)
    require(accepted['feed_sha256']==actual,'feed-receiver-feed-drift')
    previous=json.loads(feed.read_bytes());previous_time=model.validate(previous)
    require(stamp>=previous_time,'feed-receiver-older-generation')
    if stamp==previous_time:require(pin==actual,'feed-receiver-same-time-conflict')
    if pin!=actual:
        atomic(checkpoint/'delivery-previous.json',feed.read_bytes())
        transition=dict(before=actual,after=pin,source_at=payload['observed_at'],status='pending')
        write_json(pending,transition)
        atomic(feed,raw)
        accepted['feed_sha256']=pin;write_json(publication,accepted)
        transition['status']='accepted';write_json(pending,transition)
    status=dict(ok=True,sha256=pin,source_at=payload['observed_at'],received_at=now.isoformat(),
                readings=len(payload['entities']),changed=pin!=actual)
    write_json(checkpoint/'delivery-health.json',status)
    return status

def main():
    lock=None
    try:
        require(len(sys.argv)==1 and os.environ.get('SSH_ORIGINAL_COMMAND')==COMMAND,'feed-receiver-command-denied')
        connection=os.environ.get('SSH_CONNECTION','').split()
        require(len(connection)==4 and connection[0]==SOURCE and connection[2]=='192.168.1.140' and connection[3]=='22','feed-receiver-source-denied')
        signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(RuntimeError('feed-receiver-timeout')))
        signal.alarm(20)
        for directory in (ROOT,STAGE,CP,FEED.parent):secure(directory,True)
        require(digest(STAGE/'manifest.json')==MANIFEST,'feed-receiver-manifest-pin')
        members=json.loads((STAGE/'manifest.json').read_text())['files']
        require(digest(ROOT/'home_status_model.py')==members['home_status_model.py'],'feed-receiver-model-pin')
        spec=importlib.util.spec_from_file_location('approved_home_display_model',ROOT/'home_status_model.py')
        model=importlib.util.module_from_spec(spec);sys.modules[spec.name]=model;spec.loader.exec_module(model)
        lock=os.open(str(STAGE/'deploy.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raw=sys.stdin.buffer.read(262145)
        result=receive(raw,model)
        print(json.dumps(result,separators=(',',':')))
        return 0
    except Exception:
        # Never echo request bytes, exception text, attributes or SSH input.
        print('{"ok":false,"code":"feed-receiver-denied"}')
        return 1
    finally:
        signal.alarm(0)
        if lock is not None:os.close(lock)

if __name__=='__main__':raise SystemExit(main())
