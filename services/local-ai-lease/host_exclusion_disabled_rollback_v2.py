"""Rollback the exact two-root disabled install, including a partial install.

This is a local, separately reviewed recovery helper. Importing it has no
effect; the CLI must be invoked explicitly after a failed disabled install.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

ROOT=Path('/var/lib/local-ai-lab')
CHECKPOINT_OWNER_UID=0
L=Path('/usr/local/libexec/local-ai-lease')
A=Path('/usr/local/libexec/aster-a1')
OLD={
    L/'retained_archive_producer_candidate.py':'f3ae1a83f16e5b9c1bca571826029603e4c8d88fc6b529bfe79ffcd465288a3b',
    L/'lease_controller_candidate.py':'e5d328937ea482de4b365e0be1869cabd3cd589eae86a2240b1d72bd5ae47226',
    L/'full_stop_acquire_candidate.py':'bb0e1a2cc1efa2c904d374a9fc4c5cac5891bf69d63b689e2c130fa84ccd9e3b',
    A/'application_b60_controller.py':'3daa4204b1e9515e397680dc51bb2ed96994d2a273e0c2c3ef87f728ce6a41af',
}
NEW={
    L/'host_exclusion.py':'f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563',
    A/'host_exclusion.py':'f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563',
    L/'retained_archive_timing_observer.py':'f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363',
    L/'retained_archive_producer_candidate.py':'7e9b82a0c5216aad99ca1350849abb486a482586548c00ae6d7b6f309a1516c8',
    L/'lease_controller_candidate.py':'f46509e49227cf7ba78ce662184722192059277202e7315616d12456f0385217',
    L/'full_stop_acquire_candidate.py':'5859aba6cccb8f0eb8a971ccc4e3ff7054c1039482f0838c800ed7a10fc0f791',
    A/'application_b60_controller.py':'ac5667add59acd7d3d767b1abebfa11f24315ec4edd9c1e4ddf75a7a366eb4ac',
}
STATE=(ROOT/'lease.json',ROOT/'lease.lock',ROOT/'application-b60/application-b60.json',ROOT/'application-b60/application-b60.lock')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def rollback() -> dict[str, object]:
    if os.geteuid()!=0:raise RuntimeError('root required')
    checkpoints=list(ROOT.glob('host-exclusion-v2-checkpoint.*'))
    if len(checkpoints)!=1:raise RuntimeError('expected exactly one v2 checkpoint')
    checkpoint=checkpoints[0]
    info=checkpoint.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=CHECKPOINT_OWNER_UID or stat.S_IMODE(info.st_mode)!=0o700:
        raise RuntimeError('checkpoint custody differs')
    fd=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any(os.path.lexists(p) for p in STATE):
            raise RuntimeError('lease state/lock appeared; do not swap modules')
        # Installation may stop after any atomic replacement. Allow only the
        # known old/new bytes (or absence for an add); never overwrite drift.
        for path,expected in NEW.items():
            if path in OLD:
                if (not path.is_file() or path.is_symlink() or path.stat().st_nlink != 1 or
                        sha(path) not in (OLD[path],expected)):
                    raise RuntimeError('replacement differs: '+str(path))
            elif os.path.lexists(path) and (not path.is_file() or path.is_symlink() or
                                           path.stat().st_nlink != 1 or sha(path)!=expected):
                raise RuntimeError('added file differs: '+str(path))
        for path,expected in OLD.items():
            label=('L-' if path.parent==L else 'A-')+path.name
            if sha(checkpoint/label)!=expected:raise RuntimeError('checkpoint file changed: '+label)
        for path in OLD:
            label=('L-' if path.parent==L else 'A-')+path.name
            tempfd,temp=tempfile.mkstemp(prefix='.host-exclusion-v2-restore.',dir=path.parent)
            try:
                os.fchown(tempfd,0,0);os.fchmod(tempfd,0o644)
                with os.fdopen(tempfd,'wb') as stream:
                    stream.write((checkpoint/label).read_bytes())
                    stream.flush();os.fsync(stream.fileno())
                os.replace(temp,path)
            finally:
                if os.path.lexists(temp):os.unlink(temp)
        for path in NEW.keys()-OLD.keys():
            if os.path.lexists(path):path.unlink()
        for directory in (L,A):
            dirfd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY);os.fsync(dirfd);os.close(dirfd)
        if any(sha(p)!=h for p,h in OLD.items()) or any(os.path.lexists(p) for p in NEW.keys()-OLD.keys()):
            raise RuntimeError('rollback verification failed')
        return {'state':'rolled-back','checkpoint':str(checkpoint),
                'old_hashes':{str(p):h for p,h in OLD.items()},
                'new_paths_absent':sorted(str(p) for p in NEW.keys()-OLD.keys()),
                'lease_paths_absent':True}
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)


if __name__ == '__main__':
    print(json.dumps(rollback(),sort_keys=True))
