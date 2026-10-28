#!/usr/bin/env python3
"""Repair production Search catalogue activation and centre its two pills."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


ROOT = Path("/storage/.kodi/addons")
SKIN = ROOT / "skin.asterhome"
SELECT = SKIN / "tools/select_dispatch.py"
SEARCH = SKIN / "1080i/custom_1127_search.xml"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-search-catalogue-repair2")
SELECT_PREDECESSOR = "2c17107e38055ac83cddc5d75c22878991c1ecf990ee321039b1e03472ea843c"
SEARCH_PREDECESSOR = "cbf80fd89bf06bb55601a3edec328d87a14a79e40fb59d5ec02dfe05a834a9b4"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def require(value, code):
    if not value:
        raise RuntimeError(code)


def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-search-catalogue-",
                                             dir=path.parent)
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


def candidates(select_before, search_before):
    select_marker = b"    if window_id in MUSIC_WINDOWS and focus_id == 500:\n"
    select_route = (b"    if window_id == 11127 and focus_id == 51:\n"
                    b"        return 'RunScript(script.asterseerr)'\n")
    require(select_before.count(select_marker) == 1
            and select_route not in select_before, "search-select-predecessor")
    select_after = select_before.replace(select_marker, select_route + select_marker, 1)

    library = (b'<texturenofocus border="20" colordiffuse="cc202b25">'
               b'special://skin/media/ui-panel.png</texturenofocus>'
               b'<onclick>SetFocus(10)</onclick>')
    catalogue = (b'<texturenofocus border="20" colordiffuse="cc202b25">'
                 b'special://skin/media/ui-panel.png</texturenofocus>'
                 b'<onclick>RunScript(script.asterseerr)</onclick>')
    alignment = b'<align>center</align><aligny>center</aligny>'
    require(search_before.count(library) == 1 and search_before.count(catalogue) == 1
            and alignment not in search_before.split(b'<control type="button" id="50">', 1)[1]
                .split(b'</control>', 1)[0], "search-pill-predecessor")
    search_after = search_before.replace(
        library, library.replace(b'<onclick>', alignment + b'<onclick>'), 1)
    search_after = search_after.replace(
        catalogue, catalogue.replace(b'<onclick>', alignment + b'<onclick>'), 1)
    return select_after, search_after


def main():
    require(os.uname().nodename == "AsterTVProd", "production-only")
    require(not CHECKPOINT.exists(), "search-catalogue-checkpoint-exists")
    for path in (SELECT, SEARCH, FAMILY):
        require(path.is_file() and not path.is_symlink(), "search-catalogue-file")
    select_before, search_before, family_before = (
        SELECT.read_bytes(), SEARCH.read_bytes(), FAMILY.read_bytes())
    require(sha(select_before) == SELECT_PREDECESSOR
            and sha(search_before) == SEARCH_PREDECESSOR,
            "search-catalogue-live-predecessor")
    select_after, search_after = candidates(select_before, search_before)
    family = json.loads(family_before)
    require(family["skin"]["tools/select_dispatch.py"] == sha(select_before)
            and family["skin"]["1080i/custom_1127_search.xml"] == sha(search_before),
            "search-catalogue-family-predecessor")
    family["skin"]["tools/select_dispatch.py"] = sha(select_after)
    family["skin"]["1080i/custom_1127_search.xml"] = sha(search_after)
    family_after = encoded(family)
    before = {"tools/select_dispatch.py": (SELECT, select_before),
              "1080i/custom_1127_search.xml": (SEARCH, search_before),
              "family-manifest.json": (FAMILY, family_before)}
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for relative, (_, raw) in before.items():
        target = CHECKPOINT / "before" / relative
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(raw)
    (CHECKPOINT / "state.json").write_text('{"state":"prepared"}\n')
    try:
        atomic(SELECT, select_after)
        atomic(SEARCH, search_after)
        atomic(FAMILY, family_after)
        require(SELECT.read_bytes() == select_after and SEARCH.read_bytes() == search_after
                and FAMILY.read_bytes() == family_after, "search-catalogue-install")
        (CHECKPOINT / "state.json").write_text('{"state":"installed"}\n')
    except Exception:
        for _, (path, raw) in before.items():
            atomic(path, raw)
        (CHECKPOINT / "state.json").write_text('{"state":"rolled-back"}\n')
        raise
    print(json.dumps({"installed": True, "select_sha256": sha(select_after),
                      "search_sha256": sha(search_after),
                      "family_sha256": sha(family_after)}, sort_keys=True))


if __name__ == "__main__":
    main()
