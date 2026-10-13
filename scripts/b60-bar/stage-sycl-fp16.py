#!/usr/bin/env python3
"""Privately extract publisher-verified b11429 FP16 build; no GPU initialization."""
import hashlib
import json
import os
import shutil
import tarfile
from pathlib import Path, PurePosixPath

BASE=Path('/dev/shm/b60-sycl-assets-20261010')
ARCHIVE=BASE/'packages'/'llama-b11429-bin-ubuntu-sycl-fp16-x64.tar.gz'
DEST=BASE/'llama-sycl-fp16'
NAMESPACE=Path('/opt/b60-level-zero-trial-20261010/llama-sycl-fp16')
EXPECTED='dbbf6e0d767b3da3b4f13c7fa8bb49582cdd427b800e060d0958568c8c4fc973'
def validate_members(members):
    for member in members:
        path=PurePosixPath(member.name)
        assert not path.is_absolute() and path.parts[0]=='llama-b11429'
        assert '..' not in path.parts and (member.isfile() or member.isdir() or member.issym() or member.islnk())
        if member.issym() or member.islnk():
            link=PurePosixPath(member.linkname)
            assert not link.is_absolute() and '..' not in link.parts
    return sum(m.size for m in members if m.isfile())
def digest(path):
    sha=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): sha.update(chunk)
    return sha.hexdigest()
def main():
    assert not DEST.exists() and not NAMESPACE.exists()
    assert ARCHIVE.stat().st_size==54298316 and digest(ARCHIVE)==EXPECTED
    with tarfile.open(ARCHIVE,'r:gz') as tar:
        members=tar.getmembers()
        total=validate_members(members)
        memory=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
        assert int(memory['MemAvailable'].split()[0])*1024 >= 4*1024**3 + total*2
        assert shutil.disk_usage(BASE).free >= total*2
        DEST.mkdir(mode=0o755)
        tar.extractall(DEST,filter='data')
    server=DEST/'llama-b11429'/'llama-server'
    backend=DEST/'llama-b11429'/'libggml-sycl.so.0.26.0'
    assert digest(server)=='0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5'
    assert digest(backend)=='58757946256db139bab7ddab56dbe6e8d5503bb41518eb25bfc734c175c68591'
    NAMESPACE.symlink_to(DEST,target_is_directory=True)
    record=dict(publisher_archive_sha256=EXPECTED,archive_bytes=54298316,
                unpacked_bytes=total,server_sha256=digest(server),backend_sha256=digest(backend),
                precision='fp16',private_namespace=str(NAMESPACE),ram_backed_path=str(DEST),
                system_installation=False,gpu_initialized=False)
    raw=(json.dumps(record,sort_keys=True)+'\n').encode()
    path=BASE/'fp16-stage-proof.json'
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    print(json.dumps(dict(staging=record,proof_sha256=hashlib.sha256(raw).hexdigest()),sort_keys=True))
if __name__=='__main__': main()
