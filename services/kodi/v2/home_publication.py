"""One-use, private Home file trial with checkpoint and foreign-write fences.

No network or Kodi calls. Callers supply an idle guard and fixed reviewed paths.
The root-owned trial assumes no concurrent privileged feed writer; checks fence
observed drift, not a cross-process compare-and-swap guarantee.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from home_delivery import SOURCE_KEYS, unique_object, reject_constant
from home_dashboard_model import project

MAX_BYTES = 262144


def require(ok, code):
    if not ok: raise ValueError(code)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def read_private(path):
    path = Path(path)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'home-publish-linked')
    fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1 and
                stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_uid == os.geteuid()
                and 0 < metadata.st_size <= MAX_BYTES, 'home-publish-private-file')
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, 'home-publish-file-size')
    return raw, metadata


def validate(raw, now):
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_BYTES, 'home-publish-size')
    try:
        payload = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
        require(isinstance(payload, dict) and isinstance(payload.get('snapshot'), dict)
                and set(payload['snapshot']) == SOURCE_KEYS, 'home-publish-source-contract')
        view = project(payload, now)
        require(view.state == 'fresh', 'home-publish-' + view.state)
        return payload
    except (TypeError, KeyError, UnicodeError, RecursionError):
        raise ValueError('home-publish-invalid') from None


def exclusive(path, raw):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())


def save_state(folder, state):
    encoded = (json.dumps(state, sort_keys=True, indent=2) + '\n').encode()
    fd, name = tempfile.mkstemp(prefix='.state-', dir=folder)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, Path(folder)/'state.json')
    finally:
        if os.path.exists(name): os.unlink(name)


def load_state(folder):
    raw, _ = read_private(Path(folder)/'state.json')
    return json.loads(raw)


def checkpoint(feed, folder, expected):
    feed, folder = Path(feed), Path(folder)
    raw, metadata = read_private(feed)
    require(digest(raw) == expected, 'home-publish-before-drift')
    require(not any(p.is_symlink() for p in (folder.parent, *folder.parents)), 'home-publish-linked')
    folder.mkdir(mode=0o700)  # A previous trial must never be silently reused.
    exclusive(folder/'before.bin', raw)
    require(read_private(folder/'before.bin')[0] == raw, 'home-publish-backup-unverified')
    exclusive(folder/'isolated-restore.bin', raw)
    os.utime(folder/'isolated-restore.bin', ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
    restored, proof = read_private(folder/'isolated-restore.bin')
    require(restored == raw and proof.st_mtime_ns == metadata.st_mtime_ns,
            'home-publish-isolated-restore-failed')
    state = dict(version=1, phase='prepared', before_sha256=expected,
                 atime_ns=metadata.st_atime_ns, mtime_ns=metadata.st_mtime_ns,
                 candidate_sha256=None)
    save_state(folder, state)
    return state


def replace_if_owned(feed, raw, expected, ready, timestamps=None):
    feed = Path(feed)
    require(digest(read_private(feed)[0]) == expected, 'home-publish-foreign-write')
    fd, name = tempfile.mkstemp(prefix='.home-trial-', dir=feed.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        if timestamps is not None: os.utime(name, ns=timestamps)
        require(ready(), 'home-publish-not-idle')
        require(digest(read_private(feed)[0]) == expected, 'home-publish-foreign-write')
        os.replace(name, feed)
        directory = os.open(str(feed.parent), os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(directory)
        finally: os.close(directory)
        require(digest(read_private(feed)[0]) == digest(raw), 'home-publish-readback-failed')
    finally:
        if os.path.exists(name): os.unlink(name)


def apply(feed, folder, raw, candidate_sha256, ready, clock=lambda: datetime.now(timezone.utc)):
    require(digest(raw) == candidate_sha256, 'home-publish-candidate-drift')
    validate(raw, clock())
    state = load_state(folder)
    require(state['phase'] == 'prepared', 'home-publish-one-use-only')
    require(ready(), 'home-publish-not-idle')
    state.update(phase='apply-pending', candidate_sha256=candidate_sha256)
    save_state(folder, state)
    def checked():
        validate(raw, clock())
        return ready()
    replace_if_owned(feed, raw, state['before_sha256'], checked)
    state['phase'] = 'applied'; save_state(folder, state)


def restore(feed, folder):
    state = load_state(folder)
    raw, _ = read_private(Path(folder)/'before.bin')
    require(digest(raw) == state['before_sha256'], 'home-publish-backup-drift')
    current, _ = read_private(feed)
    current_sha = digest(current)
    require(current_sha in (state['before_sha256'], state['candidate_sha256']),
            'home-publish-foreign-write')
    state['phase'] = 'restore-pending'; save_state(folder, state)
    replace_if_owned(feed, raw, current_sha, lambda: True,
                     (state['atime_ns'], state['mtime_ns']))
    require(read_private(feed)[1].st_mtime_ns == state['mtime_ns'], 'home-publish-restore-time')
    state['phase'] = 'restored'; save_state(folder, state)
