#!/usr/bin/env python3
"""Repair stale v2 TV/search manifest pins on the production Aster box.

The repair is deliberately self-bounding: it derives the active series pin,
requires exactly one stale pin in each consumer, checkpoints every changed
file, and updates only the corresponding manifest rows.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


ROOT = Path("/storage/.kodi/addons")
RUNTIME = ROOT / "script.asterruntime"
SKIN = ROOT / "skin.asterhome"
SERIES = RUNTIME / "aster-series-preview24/manifest.json"
LAUNCHER = SKIN / "tools/aster_v2_series.py"
SEARCH = RUNTIME / "aster-global-search-ui22"
HANDOFF = SEARCH / "resources/lib/search_handoff.py"
SEARCH_MANIFEST = SEARCH / "manifest.json"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-tv-search-pin-repair1")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".aster-tv-search-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def main() -> None:
    require(os.uname().nodename == "AsterTVProd", "production-only")
    require(not CHECKPOINT.exists(), "checkpoint-exists")
    for path in (SERIES, LAUNCHER, HANDOFF, SEARCH_MANIFEST, FAMILY):
        require(path.is_file() and not path.is_symlink(), "missing-or-symlink:" + str(path))

    series_raw = SERIES.read_bytes()
    series = json.loads(series_raw)
    series_pin = sha(series_raw)
    require(series.get("component") == "aster-series-preview24", "series-component")
    require(len(series.get("files", [])) == 8, "series-file-count")

    launcher_before = LAUNCHER.read_bytes()
    launcher_pin = next(iter(__import__("re").findall(
        rb"MANIFEST_SHA='([0-9a-f]{64})'", launcher_before)), None)
    require(launcher_pin is not None and launcher_pin != series_pin,
            "launcher-pin-not-stale")
    launcher_after = launcher_before.replace(
        b"MANIFEST_SHA='" + launcher_pin + b"'",
        b"MANIFEST_SHA='" + series_pin.encode() + b"'", 1)

    handoff_before = HANDOFF.read_bytes()
    handoff_pin = next(iter(__import__("re").findall(
        rb"SERIES_SHA='([0-9a-f]{64})'", handoff_before)), None)
    require(handoff_pin is not None and handoff_pin != series_pin,
            "handoff-pin-not-stale")
    handoff_after = handoff_before.replace(
        b"SERIES_SHA='" + handoff_pin + b"'",
        b"SERIES_SHA='" + series_pin.encode() + b"'", 1)

    search_before = SEARCH_MANIFEST.read_bytes()
    search = json.loads(search_before)
    rows = [row for row in search.get("files", [])
            if row.get("path") == "resources/lib/search_handoff.py"]
    require(len(rows) == 1 and rows[0].get("sha256") == sha(handoff_before),
            "search-manifest-predecessor")
    rows[0]["bytes"] = len(handoff_after)
    rows[0]["sha256"] = sha(handoff_after)
    search_after = encoded(search)

    family_before = FAMILY.read_bytes()
    family = json.loads(family_before)
    require(family["components"]["aster-series-preview24"]["manifest_sha256"] == series_pin,
            "family-series-pin")
    family["components"]["aster-global-search-ui22"]["manifest_sha256"] = sha(search_after)
    family["skin"]["tools/aster_v2_series.py"] = sha(launcher_after)
    family_after = encoded(family)

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    before = {
        "skin/tools/aster_v2_series.py": (LAUNCHER, launcher_before),
        "addon/aster-global-search-ui22/resources/lib/search_handoff.py": (HANDOFF, handoff_before),
        "addon/aster-global-search-ui22/manifest.json": (SEARCH_MANIFEST, search_before),
        "addon/family-manifest.json": (FAMILY, family_before),
    }
    after = {
        "skin/tools/aster_v2_series.py": (LAUNCHER, launcher_after),
        "addon/aster-global-search-ui22/resources/lib/search_handoff.py": (HANDOFF, handoff_after),
        "addon/aster-global-search-ui22/manifest.json": (SEARCH_MANIFEST, search_after),
        "addon/family-manifest.json": (FAMILY, family_after),
    }
    for relative, (_, raw) in before.items():
        target = CHECKPOINT / "before" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (CHECKPOINT / "state.json").write_text(json.dumps({"state": "prepared"}) + "\n")
    try:
        for relative, (path, raw) in after.items():
            atomic(path, raw)
        require(LAUNCHER.read_bytes() == launcher_after, "launcher-install")
        require(HANDOFF.read_bytes() == handoff_after, "handoff-install")
        require(json.loads(SEARCH_MANIFEST.read_text())["files"] == json.loads(search_after)["files"],
                "search-manifest-install")
        require(json.loads(FAMILY.read_text())["components"]["aster-global-search-ui22"]["manifest_sha256"] == sha(search_after),
                "family-install")
        (CHECKPOINT / "state.json").write_text(json.dumps({"state": "installed"}) + "\n")
    except Exception:
        for relative, (path, raw) in before.items():
            atomic(path, raw)
        (CHECKPOINT / "state.json").write_text(json.dumps({"state": "rolled-back"}) + "\n")
        raise
    print(json.dumps({"installed": True, "series_pin": series_pin,
                      "search_manifest_sha256": sha(search_after),
                      "checkpoint": str(CHECKPOINT)}, sort_keys=True))


if __name__ == "__main__":
    main()
