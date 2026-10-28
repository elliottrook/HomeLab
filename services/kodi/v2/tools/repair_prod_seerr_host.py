#!/usr/bin/env python3
"""Restore production host admission after the Seerr catalogue hotfix."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


TARGET = Path("/storage/.kodi/addons/script.asterseerr/default.py")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-seerr-production-host1")
PREDECESSOR = "b9f04ce7b81ec0b9a82b0c6736c7559765771c3037bbc53e788fa1d16353f54f"
OLD = b"    if os.uname().nodename != 'AsterTV':\n"
NEW = b"    if os.uname().nodename not in ('AsterTV', 'AsterTVProd'):\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-seerr-host-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if os.uname().nodename != "AsterTVProd" or CHECKPOINT.exists():
        raise RuntimeError("seerr-production-host-boundary")
    before = TARGET.read_bytes()
    if sha(before) != PREDECESSOR or before.count(OLD) != 1 or NEW in before:
        raise RuntimeError("seerr-production-host-predecessor")
    after = before.replace(OLD, NEW, 1)
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / "before.py").write_bytes(before)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "before_sha256": sha(before), "after_sha256": sha(after),
        "target": str(TARGET),
    }, indent=2, sort_keys=True) + "\n")
    try:
        atomic(TARGET, after)
        if TARGET.read_bytes() != after:
            raise RuntimeError("seerr-production-host-install")
        (CHECKPOINT / "state").write_text("installed\n")
    except Exception:
        atomic(TARGET, before)
        (CHECKPOINT / "state").write_text("rolled-back\n")
        raise
    print(json.dumps({"installed": True, "sha256": sha(after)}, sort_keys=True))


if __name__ == "__main__":
    main()
