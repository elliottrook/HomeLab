#!/usr/bin/env python3
"""TrueNAS: receive ONE new LXC 110 archive, never overwrite/delete backups.

Input is an SSH binary stream, not a model-visible or locally saved archive.
An interrupted partial remains recognizable for manual recovery.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--name',required=True)
    p.add_argument('--bytes',required=True,type=int)
    p.add_argument('--sha256',required=True)
    a=p.parse_args()
    assert re.fullmatch(r'vzdump-lxc-110-2026_10_11-\d{2}_\d{2}_\d{2}\.tar\.zst',a.name)
    assert re.fullmatch(r'[0-9a-f]{64}',a.sha256)
    assert a.bytes>1024**3
    root=Path('/mnt/Recovery/guests/aster-lxc110')
    final=root/a.name
    partial=root/(a.name+'.b60-checkpoint-partial')
    assert not final.exists() and not partial.exists()
    assert shutil.disk_usage(root).free-a.bytes>50*1024**3
    h=hashlib.sha256();size=0
    with os.fdopen(os.open(partial,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        for chunk in iter(lambda:sys.stdin.buffer.read(4*1024*1024),b''):
            size+=len(chunk)
            assert size<=a.bytes,'oversized checkpoint stream'
            h.update(chunk);f.write(chunk)
        f.flush();os.fsync(f.fileno())
    assert size==a.bytes and h.hexdigest()==a.sha256,'incomplete or corrupt checkpoint'
    # Hard-link publication fails if another writer appeared; no overwrite.
    os.link(partial,final)
    partial.unlink()  # Only our verified duplicate link, never an existing backup.
    proof={'archive':str(final),'bytes':size,'sha256':h.hexdigest(),
           'completed_at':datetime.now(timezone.utc).isoformat(),
           'existing_backups_deleted':False,'complete':True}
    with os.fdopen(os.open(root/(a.name+'.b60-checkpoint-proof.json'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:
        json.dump(proof,f,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
    print(json.dumps(proof,sort_keys=True))

if __name__=='__main__':main()
