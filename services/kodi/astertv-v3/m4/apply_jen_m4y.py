#!/usr/bin/env python3
"""Reapply the Jen-only YouTube/lifecycle overlay after the v2 release guard."""

import hashlib
import os
import socket
from pathlib import Path


HOST = "AsterTV-Jen"
ROOT = Path("/storage/.aster-v3/m4y")
NAV = Path("/storage/.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml")
FOCUS = Path("/storage/.kodi/addons/skin.asterhome/tools/youtube_root_focus.py")
ACCOUNT = Path("/storage/.kodi/addons/script.asterprofiles.v3lab")
BASE_NAV_SHA256 = "6798822d0218b96cde69e385545ad36a425c01c455fdfcb69a5d8ab7208fcf8a"
CONTENT = (
    '<content target="videos">plugin://plugin.video.youtube/subscriptions/list/</content>',
    '<content target="videos">plugin://plugin.video.youtube/special/recommendations</content>',
    '<content target="videos">plugin://plugin.video.youtube/special/playlist/WL</content>',
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patch_nav(data):
    text = data.decode("utf-8")
    for value in CONTENT:
        if text.count(value) != 1:
            raise RuntimeError("youtube-content-anchor")
        text = text.replace(value, "", 1)
    return text.encode("utf-8")


def atomic(source, destination, mode=0o644):
    data = Path(source).read_bytes()
    temporary = destination.with_name("." + destination.name + ".m4y")
    temporary.write_bytes(data)
    os.chmod(temporary, mode)
    os.replace(temporary, destination)


def main():
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    data = NAV.read_bytes()
    if digest(data) == BASE_NAV_SHA256:
        data = patch_nav(data)
        temporary = NAV.with_name("." + NAV.name + ".m4y")
        temporary.write_bytes(data); os.chmod(temporary, 0o644); os.replace(temporary, NAV)
    elif data != patch_nav((ROOT / "MyVideoNav.base.xml").read_bytes()):
        raise RuntimeError("youtube-nav-drift")
    atomic(ROOT / "youtube_root_focus.py", FOCUS)
    atomic(ROOT / "identity_resolver.py", ACCOUNT / "identity_resolver.py")
    atomic(ROOT / "authority.py", ACCOUNT / "authority.py")
    atomic(ROOT / "registry.py", ACCOUNT / "registry.py")
    atomic(ROOT / "profile_service.py", ACCOUNT / "service.py")


if __name__ == "__main__":
    main()
