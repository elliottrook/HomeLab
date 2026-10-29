#!/usr/bin/env python3
"""Rehearse the pinned v2 add-on archive in a disposable Kodi-shaped root."""

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import xml.etree.ElementTree as ET


IDS = {
    "plugin.audio.asterbooks", "plugin.video.asterhome",
    "resource.uisounds.asterhome", "screensaver.asterhome.v2lab",
    "script.asteracquisition", "script.astermusic.v2lab",
    "script.asterruntime", "script.asterseerr", "script.astervoice.v2lab",
    "service.aster.playerui", "service.aster.startup", "skin.asterhome",
}


def inventory(archive):
    seen = set()
    roots = set()
    files = []
    for member in archive.getmembers():
        name = member.name
        if name in (".", "./"):
            continue
        if not name.startswith("./") or name in seen:
            raise ValueError("unsafe or duplicate archive name: " + name)
        seen.add(name)
        path = PurePosixPath(name[2:])
        if (path.is_absolute() or not path.parts or path.parts[0] not in IDS
                or any(part in ("", ".", "..") for part in path.parts)
                or not (member.isdir() or member.isfile())):
            raise ValueError("unsafe archive member: " + name)
        roots.add(path.parts[0])
        if member.isfile():
            files.append((member, path))
    if roots != IDS:
        raise ValueError("add-on inventory differs from release: " + repr(roots ^ IDS))
    return files


def trial(archive, files, parent, fail_after=None):
    with tempfile.TemporaryDirectory(prefix="aster-v2-rehearsal-", dir=parent) as tmp:
        root = Path(tmp)
        addons = root / "storage/.kodi/addons"
        userdata = root / "storage/.kodi/userdata"
        addons.mkdir(parents=True)
        userdata.mkdir()
        sentinel = userdata / "existing-profile.keep"
        sentinel.write_text("keep existing user data\n")
        installed = set()
        try:
            for member, relpath in files:
                target = addons.joinpath(*relpath.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError("missing archive content: " + member.name)
                with source, target.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
                installed.add(relpath.parts[0])
                if fail_after is not None and len(installed) >= fail_after:
                    raise RuntimeError("injected interrupted install")
            (addons / "skin.asterhome/fonts").mkdir()
            for addon_id in IDS:
                manifest = ET.parse(addons / addon_id / "addon.xml").getroot()
                if manifest.get("id") != addon_id:
                    raise ValueError("add-on ID mismatch: " + addon_id)
            for member, relpath in files:
                target = addons.joinpath(*relpath.parts)
                source = archive.extractfile(member)
                if source is None or hashlib.sha256(source.read()).digest() != hashlib.sha256(target.read_bytes()).digest():
                    raise ValueError("installed file differs: " + member.name)
        except RuntimeError as error:
            if str(error) != "injected interrupted install":
                raise
            if fail_after is None:
                raise
        finally:
            for addon_id in IDS:
                shutil.rmtree(addons / addon_id, ignore_errors=True)
        if list(addons.iterdir()) or sentinel.read_text() != "keep existing user data\n":
            raise ValueError("rollback left add-ons or changed user data")
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--scratch", type=Path, default=Path("/tmp"))
    args = parser.parse_args()
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != args.sha256:
        raise ValueError("archive checksum mismatch")
    if not args.scratch.is_dir():
        raise ValueError("scratch directory missing")
    with tarfile.open(args.archive, "r:gz") as archive:
        files = inventory(archive)
        count = trial(archive, files, args.scratch)
        trial(archive, files, args.scratch, fail_after=6)
    print(f"PASS: {len(IDS)} add-ons, {count} files, full and interrupted rollback; user data preserved")


if __name__ == "__main__":
    main()
