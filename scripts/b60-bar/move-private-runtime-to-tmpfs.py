#!/usr/bin/env python3
"""Move only task-derived private driver libraries; accepted production untouched."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

SOURCE=Path('/opt/b60-level-zero-trial-20261010/root')
DEST=Path('/dev/shm/b60-driver-assets-20261010/root')
def manifest(root):
    data={}
    for p in sorted(root.rglob('*')):
        name=str(p.relative_to(root))
        stat=p.lstat()
        if p.is_symlink():
            content=dict(kind='symlink',target=os.readlink(p))
        elif p.is_file():
            digest=hashlib.sha256()
            with p.open('rb') as f:
                for chunk in iter(lambda:f.read(1024*1024),b''): digest.update(chunk)
            content=dict(kind='file',size=stat.st_size,sha256=digest.hexdigest())
        else:
            assert p.is_dir(), 'unexpected special file'
            content=dict(kind='directory')
        data[name]=dict(content,mode=stat.st_mode & 0o7777,uid=stat.st_uid,gid=stat.st_gid)
    return data
def main():
    assert SOURCE.is_dir() and not SOURCE.is_symlink() and not DEST.exists()
    assert subprocess.check_output(['systemctl','is-active','aster-llama.service'],text=True).strip()=='active'
    candidate=subprocess.run(['systemctl','is-active','aster-b60-candidate.service'],capture_output=True,text=True)
    assert candidate.stdout.strip()=='inactive'
    before=manifest(SOURCE)
    size=sum(p.get('size',0) for p in before.values())
    memory=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    assert int(memory['MemAvailable'].split()[0])*1024 >= 4*1024**3 + size*2
    assert shutil.disk_usage('/dev/shm').free >= size*2
    free_before=shutil.disk_usage('/').free
    DEST.parent.mkdir(mode=0o755)
    subprocess.run(['mv','--',str(SOURCE),str(DEST)],check=True,timeout=180)
    try:
        assert manifest(DEST)==before, 'private library content/metadata drift'
        SOURCE.symlink_to(DEST,target_is_directory=True)
    except BaseException:
        if not SOURCE.exists():
            subprocess.run(['mv','--',str(DEST),str(SOURCE)],check=True,timeout=180)
        raise
    record=dict(source_namespace=str(SOURCE),ram_backed_target=str(DEST),files_and_links_verified=len(before),
                content_metadata_manifest_sha256=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
                derived_runtime_bytes=size,disk_free_before=free_before,disk_free_after=shutil.disk_usage('/').free,
                accepted_production_changed=False,volatile_trial_requires_restaging_after_reboot=True)
    raw=(json.dumps(record,sort_keys=True)+'\n').encode()
    path=DEST.parent/'migration-proof.json'
    with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    print(json.dumps(dict(migration=record,proof_sha256=hashlib.sha256(raw).hexdigest()),sort_keys=True))
if __name__=='__main__': main()
