"""Bounded regular local file read; never a network transport or publisher."""
import json
import os
from pathlib import Path
import stat

MAX_BYTES=262144


def read_payload(path):
    path=Path(path)
    try:
        if any(p.is_symlink() for p in (path,*path.parents)):return {}
        descriptor=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(descriptor,'rb') as stream:
            metadata=os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_size>MAX_BYTES:return {}
            raw=stream.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:return {}
        return json.loads(raw)
    except FileNotFoundError:return None
    except (OSError,ValueError):return {}
