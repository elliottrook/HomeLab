#!/usr/bin/env python3
"""Checkpoint and repair the lab's YouTube landing focus handoff."""

from pathlib import Path
import os
import shutil
import tempfile


NAV = Path("/storage/.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml")
HELPER = Path("/storage/.kodi/addons/skin.asterhome/tools/youtube_root_focus.py")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-youtube-root-focus-20261028.xml")
BEFORE = (
    b'<onload condition="String.IsEqual(Container.FolderPath,plugin://plugin.video.youtube/)">'
    b'AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:03,silent)</onload>'
)
AFTER = b'<onload>RunScript(special://skin/tools/youtube_root_focus.py)</onload>'


def main():
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab-host-only")
    if any(path.is_symlink() for path in (NAV, HELPER, CHECKPOINT)):
        raise RuntimeError("symlink-refused")
    if not NAV.is_file() or not HELPER.is_file() or CHECKPOINT.exists():
        raise RuntimeError("preflight-failed")
    raw = NAV.read_bytes()
    if raw.count(BEFORE) != 1 or AFTER in raw:
        raise RuntimeError("unexpected-youtube-onload")
    shutil.copy2(NAV, CHECKPOINT)
    with tempfile.NamedTemporaryFile(dir=NAV.parent, prefix=".youtube-focus-", delete=False) as tmp:
        tmp.write(raw.replace(BEFORE, AFTER, 1))
        temp = Path(tmp.name)
    try:
        os.chmod(temp, NAV.stat().st_mode)
        os.replace(temp, NAV)
    finally:
        temp.unlink(missing_ok=True)
    if NAV.read_bytes().count(AFTER) != 1:
        raise RuntimeError("youtube-focus-write-failed")
    print("lab YouTube landing focus repaired; predecessor checkpointed")


if __name__ == "__main__":
    main()
