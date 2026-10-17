"""One-use, disabled F2 file install. No scan, lease, timer or service action.

Run only after the separate three-path host-change approval and target-Linux
synthetic tests. The source bundle is pinned in the F2 release card.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


ROOT = Path('/var/lib/local-ai-lab')
STAGE = ROOT / 'f2-stage.JBV2aDou'
L = Path('/usr/local/libexec/local-ai-lease')
PLAN = (
    (Path('/usr/local/sbin/local-ai-lease'), 'lease_controller.py',
     'f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23',
     '67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c', 0o750),
    (L / 'retained_archive_producer_candidate.py', 'retained_archive_producer_candidate.py',
     '7e9b82a0c5216aad99ca1350849abb486a482586548c00ae6d7b6f309a1516c8',
     '5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb', 0o644),
    (L / 'f2_observer_runner_candidate.py', 'f2_observer_runner_candidate.py', None,
     'd50ee2207bc4185db266ad01af540b9b719397dec3855ee579ee18f983a3535d', 0o644),
)
STATE = ('lease.json', 'lease.lock', 'application-b60/application-b60.json',
         'application-b60/application-b60.lock', 'archive-integrity.json')


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _regular(path: Path, *, owner: int, mode: int, expected: str) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner
                or info.st_gid != os.getegid() or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != mode or not 0 < info.st_size < 65_536):
            raise RuntimeError('file custody differs: ' + str(path))
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            raw = stream.read(65_536)
        if _digest(raw) != expected:
            raise RuntimeError('file hash differs: ' + str(path))
        return raw
    finally:
        os.close(fd)


def _private_dir(path: Path, owner: int) -> None:
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != owner
            or info.st_gid != os.getegid() or stat.S_IMODE(info.st_mode) != 0o700):
        raise RuntimeError('directory custody differs: ' + str(path))


def _no_state(root: Path) -> None:
    if any(os.path.lexists(root / item) for item in STATE):
        raise RuntimeError('lease or receipt state appeared')


def _replace(path: Path, raw: bytes, mode: int) -> None:
    fd, name = tempfile.mkstemp(prefix='.f2-disabled-', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.lexists(name):
            os.unlink(name)


def install(*, stage: Path = STAGE, root: Path = ROOT, plan=PLAN,
            owner: int = 0) -> dict[str, object]:
    if os.geteuid() != owner or stage.parent != root:
        raise RuntimeError('root and direct private stage are required')
    _private_dir(root, owner)
    _private_dir(stage, owner)
    _private_dir(stage / 'src', owner)
    source: dict[Path, bytes] = {}
    for target, name, old, new, mode in plan:
        source[target] = _regular(stage / 'src' / name, owner=owner,
                                  mode=0o600, expected=new)
    lock_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    checkpoint = None
    replaced: list[Path] = []
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _no_state(root)
        old_bytes: dict[Path, bytes] = {}
        for target, _, old, new, mode in plan:
            if old is None:
                if os.path.lexists(target):
                    raise RuntimeError('add-only path exists: ' + str(target))
            else:
                old_bytes[target] = _regular(target, owner=owner, mode=mode,
                                             expected=old)
        checkpoint = Path(tempfile.mkdtemp(prefix='f2-disabled-checkpoint.', dir=root))
        _private_dir(checkpoint, owner)
        for target, raw in old_bytes.items():
            destination = checkpoint / target.name
            fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if _digest(destination.read_bytes()) != _digest(raw):
                raise RuntimeError('checkpoint copy differs')
        manifest = {str(path): {'old': old, 'new': new, 'mode': mode}
                    for path, _, old, new, mode in plan}
        fd = os.open(checkpoint / 'manifest.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(manifest, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        for target, _, old, new, mode in plan:
            _no_state(root)
            _replace(target, source[target], mode)
            replaced.append(target)
            _regular(target, owner=owner, mode=mode, expected=new)
        _no_state(root)
        for directory in {target.parent for target, *_ in plan} | {checkpoint}:
            fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        return {'state': 'staged-disabled', 'checkpoint': str(checkpoint),
                'path_hashes': {str(target): new for target, _, _, new, _ in plan}}
    except Exception:
        if checkpoint is not None and replaced:
            # Roll back only files this invocation replaced. Never overwrite
            # drift or a lease acquired after the lock was released.
            _no_state(root)
            for target, _, old, new, mode in reversed(plan):
                if target not in replaced:
                    continue
                _regular(target, owner=owner, mode=mode, expected=new)
                if old is None:
                    target.unlink()
                else:
                    raw = old_bytes[target]
                    if _digest(raw) != old:
                        raise RuntimeError('checkpoint source differs during rollback')
                    _replace(target, raw, mode)
                    _regular(target, owner=owner, mode=mode, expected=old)
        raise
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


if __name__ == '__main__':
    print(json.dumps(install(), sort_keys=True))
