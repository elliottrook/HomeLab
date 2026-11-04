#!/usr/bin/env python3
"""Extend accepted v2 host gates to the named low-spec test client."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile


ROOT = Path("/storage/.kodi/addons")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-low-spec-host-gates-20261104")
FILES = (
    "plugin.audio.asterbooks/resources/lib/books_sleep_ui.py",
    "plugin.audio.asterbooks/service.py",
    "screensaver.asterhome.v2lab/default.py",
    "script.asteracquisition/default.py",
    "script.astermusic.v2lab/default.py",
    "script.astermusic.v2lab/resources/lib/music_expanded_trial.py",
    "script.astermusic.v2lab/resources/lib/music_jellyfin.py",
    "script.astermusic.v2lab/resources/lib/music_trial.py",
    "script.asterruntime/aster-digest-player8/default.py",
    "script.asterruntime/aster-digest-player8/resources/lib/digest_preview_source.py",
    "script.asterruntime/aster-digest-reader6/default.py",
    "script.asterruntime/aster-global-search-ui22/default.py",
    "script.asterruntime/aster-global-search-ui22/movie.py",
    "script.asterruntime/aster-network-preview6/default.py",
    "script.asterruntime/aster-series-preview24/default.py",
    "script.asterruntime/aster-video-scrub5/default.py",
    "script.asterseerr/default.py",
    "script.astervoice.v2lab/default.py",
    "service.aster.playerui/service.py",
    "skin.asterhome/tools/aster_v2_digest.py",
    "skin.asterhome/tools/aster_v2_music.py",
    "skin.asterhome/tools/aster_v2_series.py",
    "skin.asterhome/tools/header_search.py",
    "skin.asterhome/tools/osd_choices.py",
)
PATTERNS = (
    (b"('AsterTV-Bedroom','AsterTV-Family')",
     b"('AsterTV-Bedroom','AsterTV-Family','AsterTV-Jen')"),
    (b"('AsterTV-Bedroom', 'AsterTV-Family')",
     b"('AsterTV-Bedroom', 'AsterTV-Family', 'AsterTV-Jen')"),
    (b'("AsterTV-Bedroom", "AsterTV-Family")',
     b'("AsterTV-Bedroom", "AsterTV-Family", "AsterTV-Jen")'),
    (b'("AsterTV-Family", "AsterTV-Bedroom")',
     b'("AsterTV-Family", "AsterTV-Bedroom", "AsterTV-Jen")'),
)


def atomic(path: Path, data: bytes) -> None:
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> None:
    if socket.gethostname() != "AsterTV-Jen" or os.getuid() != 0:
        raise SystemExit("AsterTV-Jen-root-only")
    if CHECKPOINT.exists():
        raise RuntimeError("low-spec-host-gates-checkpoint-exists")
    staged = {}
    for relative in FILES:
        path = ROOT / relative
        before = path.read_bytes()
        after = before
        count = 0
        for old, new in PATTERNS:
            found = after.count(old)
            after = after.replace(old, new)
            count += found
        if count < 1 or after == before or b"AsterTV-Jen" not in after:
            raise RuntimeError("low-spec-host-gate-pattern:" + relative)
        compile(after, str(path), "exec")
        staged[relative] = (before, after, count)
    bootstrap = ROOT / "script.asterbootstrap/default.py"
    before = bootstrap.read_bytes()
    old = b"os.uname().nodename != 'AsterTV-Bedroom'"
    new = b"os.uname().nodename not in ('AsterTV-Bedroom','AsterTV-Jen')"
    if before.count(old) != 1:
        raise RuntimeError("low-spec-bootstrap-pattern")
    after = before.replace(old, new)
    compile(after, str(bootstrap), "exec")
    staged["script.asterbootstrap/default.py"] = (before, after, 1)

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    report = {"host": "AsterTV-Jen", "files": {}}
    try:
        for relative, (original, updated, count) in staged.items():
            saved = CHECKPOINT / "before" / relative
            saved.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            saved.write_bytes(original)
            os.chmod(saved, 0o600)
            atomic(ROOT / relative, updated)
            report["files"][relative] = {
                "replacements": count,
                "before_sha256": hashlib.sha256(original).hexdigest(),
                "after_sha256": hashlib.sha256(updated).hexdigest(),
            }
        (CHECKPOINT / "manifest.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
        os.chmod(CHECKPOINT / "manifest.json", 0o600)
    except Exception:
        for relative, (original, _, _) in staged.items():
            atomic(ROOT / relative, original)
        raise
    print(json.dumps({"installed": True, "files": len(staged),
                      "checkpoint": str(CHECKPOINT)}, sort_keys=True))


if __name__ == "__main__":
    main()
