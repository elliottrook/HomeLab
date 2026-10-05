"""Bounded same-descriptor reads; reject symlinks in every path component."""
import os
from pathlib import Path
import stat


def read_owned_regular(path,limit):
    path=Path(path)
    if not path.is_absolute() or '..' in path.parts or type(limit) is not int or not 0<limit<=131072:
        raise ValueError('fixed absolute bounded path required')
    directory=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    fd=None
    try:
        for name in path.parts[1:-1]:
            child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
            os.close(directory);directory=child
        fd=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_uid!=os.geteuid() or
            before.st_nlink!=1 or before.st_mode&0o022 or not 0<=before.st_size<=limit):
            raise ValueError('unsafe file type/owner/mode/size')
        chunks=[];size=0
        while True:
            chunk=os.read(fd,min(8192,limit+1-size))
            if not chunk:break
            chunks.append(chunk);size+=len(chunk)
            if size>limit:raise ValueError('read limit exceeded')
        after=os.fstat(fd)
        identity=lambda s:(s.st_dev,s.st_ino,s.st_uid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        if identity(before)!=identity(after) or size!=before.st_size:raise ValueError('file changed during read')
        return b''.join(chunks)
    finally:
        if fd is not None:os.close(fd)
        os.close(directory)
