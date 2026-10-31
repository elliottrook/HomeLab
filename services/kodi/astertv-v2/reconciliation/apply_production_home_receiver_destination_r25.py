#!/usr/bin/env python3
"""Bind the restricted Home receiver to AsterTVProd's exact destination IP."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

LIVE=Path('/storage/.aster-home-delivery/receive.py')
PAYLOAD=Path('/storage/.aster-staging/aster-home-prod-r24/receive.py')
CHECKPOINT=Path('/storage/.aster-checkpoints/aster-home-delivery-prod-destination-r25')
EXPECTED='db7b9fd5466eb6c5ffd9304adda3b52d93bc45d02f2e4ca6b94c46d2d0d6e374'

def sha(data):return hashlib.sha256(data).hexdigest()
def atomic(path,data):
    fd,tmp=tempfile.mkstemp(prefix='.aster-home-r25-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main():
    if os.uname().nodename!='AsterTVProd' or CHECKPOINT.exists():raise RuntimeError('r25-boundary')
    originals={path:path.read_bytes() for path in (LIVE,PAYLOAD)}
    if any(sha(data)!=EXPECTED for data in originals.values()):raise RuntimeError('r25-source-drift')
    old="connection[2]=='192.168.1.140'"
    new="connection[2]=='192.168.1.157'"
    if any(data.decode().count(old)!=1 for data in originals.values()):raise RuntimeError('r25-source-count')
    candidates={path:data.decode().replace(old,new,1).encode() for path,data in originals.items()}
    for path,data in candidates.items():compile(data,str(path),'exec')
    CHECKPOINT.mkdir(mode=0o700,parents=True)
    for path,data in originals.items():
        saved=CHECKPOINT/(path.name+'.'+('live' if path==LIVE else 'payload')+'.before')
        saved.write_bytes(data);saved.chmod(0o600)
    try:
        for path,data in candidates.items():atomic(path,data)
        if any(sha(path.read_bytes())!=sha(data) for path,data in candidates.items()):
            raise RuntimeError('r25-post-write')
    except Exception:
        for path,data in originals.items():atomic(path,data)
        raise
    print(json.dumps({'installed':True,'checkpoint':str(CHECKPOINT),
                      'receive_sha256':sha(candidates[LIVE]),
                      'destination':'192.168.1.157'},sort_keys=True))

if __name__=='__main__':main()
