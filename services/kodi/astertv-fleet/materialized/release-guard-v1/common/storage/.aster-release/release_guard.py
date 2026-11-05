#!/usr/bin/env python3
"""Snapshot, verify, and restore the accepted AsterTV runtime.

The accepted copy lives outside Kodi's add-on tree.  Restore is intended to
run before Kodi starts, so it cannot replace code which Kodi is executing.
Only files present in the accepted manifest are restored; user data, account
data, databases, caches, and extra files are never copied or deleted.
"""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path, PurePosixPath


DEFAULT_ROOT = Path("/storage/.kodi/addons")
DEFAULT_STATE = Path("/storage/.aster-release/accepted")
MANIFEST_NAME = "accepted-manifest.json"
GUARDED = (
    "skin.asterhome",
    "script.asterruntime",
    "script.astermusic.v2lab",
    "plugin.video.astersearch",
    "service.aster.startup",
    "service.aster.reliability",
    "screensaver.asterhome.v2lab",
)
REQUIRED = frozenset(GUARDED)
IGNORED_NAMES = {"__pycache__", ".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value):
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("unsafe-relative-path")
    return relative


def iter_guarded(root):
    for name in GUARDED:
        base = root / name
        if not base.is_dir() or base.is_symlink():
            continue
        for path in sorted(base.rglob("*")):
            relative = path.relative_to(root)
            if any(part in IGNORED_NAMES for part in relative.parts):
                continue
            if path.suffix in IGNORED_SUFFIXES:
                continue
            if path.is_symlink():
                raise ValueError("guarded-symlink")
            if path.is_file():
                yield relative, path


def encode_manifest(files, host):
    return json.dumps({
        "schema": 1,
        "host": host,
        "accepted_at": int(time.time()),
        "files": files,
    }, indent=2, sort_keys=True).encode() + b"\n"


def atomic_write(path, data, mode=0o600):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def snapshot(root, state, host, allowed_missing=frozenset()):
    missing = sorted(name for name in REQUIRED
                     if name not in allowed_missing
                     and (not (root / name).is_dir() or (root / name).is_symlink()))
    if missing:
        raise ValueError("guarded-roots-missing:" + ",".join(missing))
    parent = state.parent
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".accepted-", dir=parent))
    files = []
    try:
        payload = temporary / "payload"
        for relative, source in iter_guarded(root):
            target = payload / relative
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copy2(source, target)
            files.append({
                "path": relative.as_posix(),
                "bytes": source.stat().st_size,
                "sha256": sha256(source),
            })
        atomic_write(temporary / MANIFEST_NAME, encode_manifest(files, host))
        previous = parent / (state.name + ".previous")
        if previous.exists():
            shutil.rmtree(previous)
        moved_previous = False
        if state.exists():
            os.replace(state, previous)
            moved_previous = True
        try:
            os.replace(temporary, state)
        except Exception:
            if moved_previous and previous.exists() and not state.exists():
                os.replace(previous, state)
            raise
        return {"outcome": "accepted", "files": len(files), "host": host}
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def load_manifest(state, host):
    data = json.loads((state / MANIFEST_NAME).read_text())
    if data.get("schema") != 1 or data.get("host") != host:
        raise ValueError("accepted-manifest-host-or-schema")
    rows = data.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("accepted-manifest-files")
    return data, rows


def verify(root, state, host):
    _, rows = load_manifest(state, host)
    drift = []
    for row in rows:
        relative = safe_relative(row["path"])
        target = root / relative
        if (not target.is_file() or target.is_symlink()
                or target.stat().st_size != row["bytes"]
                or sha256(target) != row["sha256"]):
            drift.append(relative.as_posix())
    return {"outcome": "clean" if not drift else "drift", "drift": drift,
            "files": len(rows), "host": host}


def restore(root, state, host):
    _, rows = load_manifest(state, host)
    restored = []
    for row in rows:
        relative = safe_relative(row["path"])
        source = state / "payload" / relative
        target = root / relative
        if (not source.is_file() or source.is_symlink()
                or source.stat().st_size != row["bytes"]
                or sha256(source) != row["sha256"]):
            raise ValueError("accepted-payload-drift")
        clean = (target.is_file() and not target.is_symlink()
                 and target.stat().st_size == row["bytes"]
                 and sha256(target) == row["sha256"])
        if clean:
            continue
        target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        data = source.read_bytes()
        atomic_write(target, data, source.stat().st_mode & 0o777)
        restored.append(relative.as_posix())
    return {"outcome": "clean" if not restored else "restored",
            "restored": restored, "files": len(rows), "host": host}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("snapshot", "verify", "restore"))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--host", required=True)
    parser.add_argument("--allow-missing-guarded", action="append", default=[])
    args = parser.parse_args(argv)
    unknown = set(args.allow_missing_guarded) - REQUIRED
    if unknown:
        parser.error("unknown guarded root: " + ",".join(sorted(unknown)))
    if args.action != "snapshot" and args.allow_missing_guarded:
        parser.error("--allow-missing-guarded is snapshot-only")
    if args.action == "snapshot":
        result = snapshot(args.root, args.state, args.host,
                          frozenset(args.allow_missing_guarded))
    else:
        operation = {"verify": verify, "restore": restore}[args.action]
        result = operation(args.root, args.state, args.host)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["outcome"] in ("accepted", "clean", "restored") else 1


if __name__ == "__main__":
    raise SystemExit(main())
