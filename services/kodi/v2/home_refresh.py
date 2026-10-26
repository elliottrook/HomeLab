"""Foreground-only local generation reader; no writes, networking or scheduler."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import stat

from home_dashboard_model import project

MAX_BYTES=262144
POLL_SECONDS=2


def identity(metadata):
    return (metadata.st_dev,metadata.st_ino,metadata.st_size,metadata.st_mtime_ns,
            metadata.st_ctime_ns,metadata.st_mode,metadata.st_uid,metadata.st_nlink)


def probe(path):
    path=Path(path)
    try:
        if any(p.is_symlink() for p in (path,*path.parents)):return ('invalid','linked')
        metadata=path.lstat()
        stamp=identity(metadata)
        if not (stat.S_ISREG(metadata.st_mode) and stat.S_IMODE(metadata.st_mode)==0o600
                and metadata.st_nlink==1 and metadata.st_uid==os.geteuid()
                and 0<metadata.st_size<=MAX_BYTES):return ('invalid',stamp)
        return ('regular',stamp)
    except FileNotFoundError:return ('missing',)
    except OSError:return ('invalid','unreadable')


def unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise ValueError('home-refresh-duplicate-field')
        value[key]=item
    return value


def constant(_value):raise ValueError('home-refresh-nonfinite')


def read_generation(path,stamp):
    """Read exactly the probed generation or fail closed on concurrent replacement."""
    try:
        if stamp[0]!='regular' or probe(path)!=stamp:return {}
        descriptor=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(descriptor,'rb') as stream:
            if identity(os.fstat(stream.fileno()))!=stamp[1]:return {}
            raw=stream.read(MAX_BYTES+1)
            if identity(os.fstat(stream.fileno()))!=stamp[1]:return {}
        if len(raw)>MAX_BYTES or probe(path)!=stamp:return {}
        return json.loads(raw,object_pairs_hook=unique,parse_constant=constant)
    except (OSError,ValueError,UnicodeError,RecursionError):return {}


def timestamp(value):return datetime.fromisoformat(value.replace('Z','+00:00'))


class Consumer:
    """Retains approved values only in memory; rejects regressions until reopened.

    Stamps are change hints, not a filesystem watcher or an adversarial same-root
    integrity boundary. No concurrent privileged publisher is assumed to forge
    timestamps/inodes; source/publication clocks and schema are checked separately.
    """
    def __init__(self,path):
        self.path=Path(path);self.stamp=None;self.next_probe=0
        self.payload=None;self.highwater=None;self.last_accepted=None
        self.reads=0;self.generations=0;self.load_status='missing'

    def update(self,now,monotonic,force=False):
        if force or monotonic>=self.next_probe:
            self.next_probe=monotonic+POLL_SECONDS
            stamp=probe(self.path)
            if force or stamp!=self.stamp:
                self.stamp=stamp
                if stamp[0]=='missing':
                    self.payload=None;self.load_status='missing'
                elif stamp[0]!='regular':
                    self.payload={};self.load_status='invalid-file'
                else:
                    self.reads+=1
                    candidate=read_generation(self.path,stamp)
                    view=project(candidate,now)
                    if view.state!='fresh':
                        # Keep only timestamps/schema for expiry/future classification,
                        # never unknown attributes or rejected household values.
                        self.payload=({k:candidate[k] for k in ('schema_version','generated_at','source_updated_at')}
                            | {'snapshot':{'schema_version':3}}) if view.state in ('stale','future') else {}
                        self.load_status=view.state
                    else:
                        clocks=(timestamp(candidate['source_updated_at']),timestamp(candidate['generated_at']))
                        if self.highwater and any(a<b for a,b in zip(clocks,self.highwater)):
                            self.payload={};self.load_status='older-generation'
                        else:
                            fingerprint=hashlib.sha256(json.dumps(candidate,sort_keys=True,
                                ensure_ascii=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()
                            if fingerprint!=self.last_accepted:self.generations+=1
                            self.highwater=clocks;self.payload=candidate;self.last_accepted=fingerprint
                            self.load_status='accepted'
        return project(self.payload,now)
