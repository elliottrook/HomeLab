"""Explicit local state owner. No daemon, socket, model dispatch or credentials."""
import fcntl
import os
import stat
from pathlib import Path

if __package__:
    from .store import DispatchStore
else:
    from store import DispatchStore


def private_file(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        os.close(fd)
        raise ValueError("State file must be private and owned by the worker")
    return fd


class Runtime:
    def __init__(self, directory):
        path = Path(directory)
        if not path.is_absolute() or path.is_symlink():
            raise ValueError("Expected absolute non-symlink state directory")
        path.mkdir(mode=0o700, parents=False, exist_ok=True)
        info = path.stat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError("State directory must be private and owned by the worker")
        self.lock = private_file(path/'worker.lock')
        self.store = None
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fd = private_file(path/'jobs.sqlite')
            os.close(fd)
            self.store = DispatchStore(path/'jobs.sqlite')
            self.store.recover_startup()
        except Exception:
            if self.store is not None:
                self.store.close()
            os.close(self.lock)
            self.lock = None
            raise

    def close(self):
        if self.lock is None:
            return
        try:
            self.store.recover_startup()  # Conservative shutdown state, never 'stopped'.
        finally:
            self.store.close()
            os.close(self.lock)
            self.lock = None


def open_runtime(directory, *, enabled=False):
    # Disabled means no directory, database, process or network side effect.
    return Runtime(directory) if enabled else None
