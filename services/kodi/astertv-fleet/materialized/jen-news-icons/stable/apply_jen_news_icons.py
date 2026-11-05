#!/usr/bin/env python3
"""Reapply the Jen-only M5 News icon overlay after the release/M4 overlays."""

import hashlib
import os
import socket
from pathlib import Path


HOST = "AsterTV-Jen"
ROOT = Path("/storage/.aster-v3/m5n")
NEWS = Path("/storage/.kodi/addons/skin.asterhome/1080i/custom_1111_digest.xml")
BASE_SHA256 = "960645920dc25fd709c0310b178057afaae16fa5260404110b03fda98669cd77"
PILLS = (
    (310, 562, 39, ""),
    (311, 784, 39, ""),
    (312, 1016, 39, ""),
    (301, 1248, 39, "<onright>139</onright>"),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def icon(control_id, left, top):
    return (f'<control type="image" id="{control_id + 9000}"><left>{left}</left>'
            f'<top>{top}</top><width>30</width><height>30</height>'
            '<texture>special://skin/media/aster-compass-128.png</texture>'
            '<aspectratio>keep</aspectratio></control>')


def patch_news(data):
    text = data.decode("utf-8")
    for control_id, left, top, between in PILLS:
        anchor = (f'<textoffsetx>0</textoffsetx>{between}'
                  f'<onup>{control_id}</onup></control>')
        if text.count(anchor) != 1:
            raise RuntimeError("news-pill-anchor:" + str(control_id))
        replacement = (f'<textoffsetx>20</textoffsetx>{between}'
                       f'<onup>{control_id}</onup></control>'
                       f'{icon(control_id, left, top)}')
        text = text.replace(anchor, replacement, 1)
    return text.encode("utf-8")


def main():
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    data = NEWS.read_bytes()
    base = (ROOT / "News.base.xml").read_bytes()
    if digest(base) != BASE_SHA256:
        raise RuntimeError("news-stable-base-drift")
    expected = patch_news(base)
    if digest(data) == BASE_SHA256:
        temporary = NEWS.with_name("." + NEWS.name + ".m5n")
        temporary.write_bytes(expected)
        os.chmod(temporary, 0o644)
        os.replace(temporary, NEWS)
    elif data != expected:
        raise RuntimeError("news-live-drift")


if __name__ == "__main__":
    main()
