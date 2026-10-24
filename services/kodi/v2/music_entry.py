"""Small ID-only normal-page entry boundary and single-owner admission lock."""
from contextlib import contextmanager
import fcntl
import os
import re
from pathlib import Path
from music_playlist_save import uuid,PlaylistSaveUnavailable


def parse_entry(arguments):
    if not arguments:return 'pilot',None
    if len(arguments)==1 and arguments[0] in ('genres','shuffle'):return arguments[0],None
    if len(arguments)!=2:raise ValueError('invalid-music-entry')
    kind,value=arguments
    if kind in ('album','song') and isinstance(value,str) and re.fullmatch('[0-9]{1,10}',value):
        number=int(value)
        if 0<number<=2147483647:return kind,number
    if kind=='playlist':
        try:return kind,uuid(value)
        except PlaylistSaveUnavailable:pass
    raise ValueError('invalid-music-entry')


@contextmanager
def entry_lock(directory):
    """No stale grant/replay: flock is released even when Kodi terminates."""
    path=Path(directory)/'entry.lock';path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    descriptor=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        try:fcntl.flock(descriptor,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('music-already-open') from None
        yield
    finally:os.close(descriptor)
