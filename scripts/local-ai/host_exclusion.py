"""Source-only host exclusion primitive for archive scans and lease admission.

An advisory lock on the existing private state directory creates no lock file.
The installed manual helper (hash recorded in the Stream A read-only evidence)
uses the same directory flock during its acquisition call. That is only an
acquisition-time boundary: the phased full-drain CLI releases its flock
between commands, and the manual helper does not inspect the candidate's
separate full-drain lock directory. Recurring live use therefore still needs
a persistent supervisor or an explicit legacy-controller admission change.
"""

from __future__ import annotations

import fcntl
import os
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class HostExclusionError(RuntimeError):
    """The shared host exclusion cannot be safely acquired."""


@contextmanager
def host_exclusion(root: Path) -> Iterator[None]:
    """Hold a nonblocking exclusive lock on the root-owned mode-0700 directory."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(root, flags)
    except OSError as exc:
        raise HostExclusionError("host exclusion directory is unavailable") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o700):
            raise HostExclusionError("host exclusion directory custody is invalid")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise HostExclusionError("host exclusion is held or unavailable") from exc
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
