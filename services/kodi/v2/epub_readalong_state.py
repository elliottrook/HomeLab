"""Private, hash-bound synthetic reading position. Never shared progress."""
import json
import os
from pathlib import Path
import re
import stat
import uuid

def require(ok,code):
    if not ok:raise ValueError(code)
def identity(value):return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value)
def directory(root):
    path=Path(root)
    if path.exists():
        meta=path.lstat();require(stat.S_ISDIR(meta.st_mode) and not path.is_symlink(),'epub-state-directory')
    else:
        parent=path.parent;meta=parent.lstat()
        require(stat.S_ISDIR(meta.st_mode) and not parent.is_symlink(),'epub-state-parent')
        path.mkdir(mode=0o700)
    path.chmod(0o700);return path
def validate(value,book,chapter,audio,total):
    require(type(value) is dict and set(value)=={'schema','book','chapter','audio','sample','complete'},'epub-state-schema')
    require(value['schema']==1 and value['book']==book and value['chapter']==chapter and value['audio']==audio,'epub-state-identity')
    require(type(value['sample']) is int and 0<=value['sample']<=total and type(value['complete']) is bool,'epub-state-position')
    return value
def load(root,book,chapter,audio,total):
    path=directory(root)/'position.json'
    if not path.exists():return dict(schema=1,book=book,chapter=chapter,audio=audio,sample=0,complete=False)
    meta=path.lstat();require(stat.S_ISREG(meta.st_mode) and not path.is_symlink() and meta.st_size<=4096,'epub-state-file')
    return validate(json.loads(path.read_text()),book,chapter,audio,total)
def save(root,value,book,chapter,audio,total):
    value=validate(value,book,chapter,audio,total);folder=directory(root);target=folder/'position.json'
    temp=folder/('position-'+uuid.uuid4().hex+'.tmp')
    fd=os.open(str(temp),os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
    try:
        with os.fdopen(fd,'w') as stream:json.dump(value,stream,sort_keys=True);stream.write('\n');stream.flush();os.fsync(stream.fileno())
        os.replace(str(temp),str(target));target.chmod(0o600)
    finally:
        if temp.exists():temp.unlink()
def clear(root,book,chapter,audio,total):
    folder=directory(root);path=folder/'position.json'
    if not path.exists():return False
    load(root,book,chapter,audio,total);path.unlink();return True
