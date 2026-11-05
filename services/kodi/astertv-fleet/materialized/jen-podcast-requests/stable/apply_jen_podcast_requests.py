#!/usr/bin/env python3
"""Reapply Jen's bounded podcast-request UI after the release guard."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import socket


HOST = "AsterTV-Jen"
ROOT = Path("/storage/.aster-v3/m5p")
SKIN = Path("/storage/.kodi/addons/skin.asterhome")
INCLUDES = SKIN / "1080i/IncludesBooks.xml"
PODCASTS = SKIN / "1080i/custom_1120_podcasts.xml"
ADDON = Path("/storage/.kodi/addons/script.astertv.podcast.requests")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_includes(data: bytes) -> bytes:
    text = data.decode("utf-8")
    anchors = {
        '    <param name="browsevisible" default="true" />':
            '    <param name="browsevisible" default="true" />\n'
            '    <param name="requestvisible" default="false" />\n'
            '    <param name="requestdown" default="500" />',
        '<control type="button" id="302"><left>1560</left><top>780</top><label>Clear search</label>':
            '<control type="button" id="302"><left>1560</left><top>780</top><label>Clear search</label>',
        '<onup>301</onup><ondown>500</ondown></control>\n'
        '          <control type="label"><left>1560</left><top>880</top>':
            '<onup>301</onup><ondown>$PARAM[requestdown]</ondown></control>\n'
            '          <control type="image"><left>1560</left><top>852</top><width>260</width><height>58</height><texture border="20" colordiffuse="ffad8a4d">special://skin/media/ui-compact-card-ring.png</texture><visible>$PARAM[requestvisible]</visible></control>\n'
            '          <control type="button" id="303"><left>1562</left><top>854</top><width>256</width><height>54</height><label>Request a podcast</label><font>font20</font><align>center</align><aligny>center</aligny><textcolor>fff3eee5</textcolor><focusedcolor>fff3eee5</focusedcolor><texturefocus border="18" colordiffuse="ff005c46">special://skin/media/ui-panel.png</texturefocus><texturenofocus border="18" colordiffuse="99000000">special://skin/media/ui-panel.png</texturenofocus><onleft>500</onleft><onright>8999</onright><onup>302</onup><ondown>500</ondown><onclick>RunAddon(script.astertv.podcast.requests)</onclick><visible>$PARAM[requestvisible]</visible></control>\n'
            '          <control type="label"><left>1560</left><top>930</top>',
    }
    if 'id="303"' in text and 'name="requestvisible"' in text:
        return data
    for old, new in anchors.items():
        if text.count(old) != 1:
            raise RuntimeError("includes-anchor")
        text = text.replace(old, new, 1)
    text = text.replace('top>930</top><width>260</width><height>100</height><label>Searches the current',
                        'top>930</top><width>260</width><height>80</height><label>Searches the current', 1)
    return text.encode("utf-8")


def patch_podcasts(data: bytes) -> bytes:
    text = data.decode("utf-8")
    if 'requestvisible' in text:
        return data
    anchor = '      <param name="activeleft" value="1098" />'
    replacement = (anchor + '\n      <param name="requestvisible" value="true" />'
                   '\n      <param name="requestdown" value="303" />')
    if text.count(anchor) != 1:
        raise RuntimeError("podcasts-anchor")
    return text.replace(anchor, replacement, 1).encode("utf-8")


def atomic_bytes(destination: Path, data: bytes, mode: int = 0o644) -> None:
    temporary = destination.with_name("." + destination.name + ".m5p")
    temporary.write_bytes(data)
    os.chmod(temporary, mode)
    os.replace(temporary, destination)


def replace_tree(source: Path, destination: Path) -> None:
    staging = destination.with_name("." + destination.name + ".m5p")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(source, staging)
    for path in staging.rglob("*"):
        if path.is_symlink():
            raise RuntimeError("addon-symlink")
        if path.is_file():
            os.chmod(path, 0o644)
    if destination.exists():
        shutil.rmtree(destination)
    os.replace(staging, destination)


def main() -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    include_base = (ROOT / "IncludesBooks.base.xml").read_bytes()
    podcast_base = (ROOT / "custom_1120_podcasts.base.xml").read_bytes()
    include_expected = {digest(include_base), digest(patch_includes(include_base))}
    podcast_expected = {digest(podcast_base), digest(patch_podcasts(podcast_base))}
    if digest(INCLUDES.read_bytes()) not in include_expected:
        raise RuntimeError("includes-drift")
    if digest(PODCASTS.read_bytes()) not in podcast_expected:
        raise RuntimeError("podcasts-drift")
    atomic_bytes(INCLUDES, patch_includes(include_base))
    atomic_bytes(PODCASTS, patch_podcasts(podcast_base))
    replace_tree(ROOT / "script.astertv.podcast.requests", ADDON)


if __name__ == "__main__":
    main()
