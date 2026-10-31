#!/usr/bin/env python3
"""Migrate the bounded Aster Music playback marker after the final host rename."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile


MARKER = Path(
    "/storage/.kodi/userdata/addon_data/"
    "script.astermusic.v2lab/normal-playback.json"
)
CHECKPOINT_ROOT = Path("/storage/.aster-checkpoints")
RECOVERY_GUARD = Path("/storage/.aster-recovery-required")
TARGETS = {
    "AsterTV-Bedroom": "AsterTV",
    "AsterTV-Family": "AsterTVProd",
}


def encoded(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode()


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-music-identity-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    host = os.uname().nodename
    if host not in TARGETS:
        raise RuntimeError("AsterTV Family/Bedroom host only")
    if RECOVERY_GUARD.exists():
        raise RuntimeError("recovery guard")

    original = MARKER.read_bytes()
    value = json.loads(original)
    expected = {
        "enabled": True,
        "host": TARGETS[host],
        "queue_limit": 20000,
    }
    current = {
        "enabled": True,
        "host": host,
        "queue_limit": 20000,
    }
    if value == current:
        print(json.dumps({"changed": False, "host": host, "marker": str(MARKER)}))
        return
    if value != expected:
        raise RuntimeError("unexpected music capability marker")

    checkpoint = CHECKPOINT_ROOT / ("aster-music-identity-" + host)
    checkpoint.mkdir(mode=0o700, parents=True, exist_ok=False)
    saved = checkpoint / "normal-playback.json.before"
    saved.write_bytes(original)
    saved.chmod(0o600)

    candidate = encoded(current)
    try:
        atomic_write(MARKER, candidate)
        if MARKER.read_bytes() != candidate:
            raise RuntimeError("post-write verification failed")
    except Exception:
        atomic_write(MARKER, original)
        raise

    print(json.dumps({
        "changed": True,
        "checkpoint": str(checkpoint),
        "host": host,
        "marker": str(MARKER),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
