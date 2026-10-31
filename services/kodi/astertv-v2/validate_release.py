#!/usr/bin/env python3
"""Fail closed if the immutable AsterTV v2.0.7 production release drifts."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ARCHIVE = REPO / "services/kodi/dist/astertv-v2.0.7-production-2026-10-30-r19.tar.gz"
SIDECAR = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
PREFIX = "aster-v2-package/"
RELEASE = "astertv-v2.0.7-production-2026-10-30-r19"
SPLASH_SHA = "912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def member(bundle: tarfile.TarFile, relative: str) -> bytes:
    stream = bundle.extractfile(PREFIX + relative)
    assert stream is not None, relative
    return stream.read()


sidecar_hash, sidecar_name = SIDECAR.read_text().split()
assert sidecar_name == ARCHIVE.name
assert sha(ARCHIVE.read_bytes()) == sidecar_hash

with tarfile.open(ARCHIVE, "r:gz") as bundle:
    release = json.loads(member(bundle, "manifest.json"))
    snapshot_bytes = member(bundle, "lab-addon-snapshot-manifest.json")
    snapshot = json.loads(snapshot_bytes)
    assert release["release"] == RELEASE and snapshot["release"] == RELEASE
    assert release["status"] == "production-candidate"
    assert release["credentials_included"] is False
    assert release["profile_or_addon_data_included"] is False
    assert release["audio_configuration_included"] is False
    assert snapshot["credentials_included"] is False
    assert snapshot["Kodi profile/addon_data included"] is False
    assert len(snapshot["files"]) == release["snapshot_files"] == 577
    assert sha(snapshot_bytes) == release["artifacts"]["lab-addon-snapshot-manifest.json"]

    inventory = {row["path"]: row for row in snapshot["files"]}
    for path, row in inventory.items():
        assert "addon_data" not in Path(path).parts, path
        data = member(bundle, "lab-addon-snapshot/" + path)
        assert len(data) == row["bytes"] and sha(data) == row["sha256"], path
        if path.startswith("skin.asterhome/") and path.endswith(".xml"):
            ET.fromstring(data)
        if path.endswith(".py"):
            compile(data, path, "exec")

    splash = member(bundle, "profile-overlay/media/Splash.png")
    keymap = member(bundle, "reconciliation/payload/userdata/keymaps/g20s-pro-plus.xml")
    promoter = member(bundle, "reconciliation/promote_v207_to_production.py")
    assert sha(splash) == SPLASH_SHA == release["artifacts"]["profile-overlay/media/Splash.png"]
    assert sha(keymap) == release["artifacts"]["reconciliation/payload/userdata/keymaps/g20s-pro-plus.xml"]
    assert sha(promoter) == release["artifacts"]["reconciliation/promote_v207_to_production.py"]
    ET.fromstring(keymap)
    compile(promoter, "promote_v207_to_production.py", "exec")

    def addon(path: str) -> str:
        return member(bundle, "lab-addon-snapshot/" + path).decode()

    music = addon("skin.asterhome/1080i/IncludesMusic.xml")
    requests = addon("skin.asterhome/1080i/custom_1132_requests.xml")
    acquisition = addon("skin.asterhome/1080i/custom_1133_acquisition.xml")
    dispatcher = addon("skin.asterhome/tools/select_dispatch.py")
    seerr = addon("script.asterseerr/default.py")
    youtube = addon("skin.asterhome/1080i/MyVideoNav.xml")
    series = addon("script.asterruntime/aster-series-preview24/default.py")
    series_xml = addon("script.asterruntime/aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml")
    books_service = addon("plugin.audio.asterbooks/service.py")
    books_bridge = addon("plugin.audio.asterbooks/resources/lib/books_sync_bridge.py")
    publication = member(bundle, "epub-consumer/reader/runtime/epub_narration/publication.py").decode()

    # Final Music acceptance: text-safe pills, Media-style header, no legacy underline.
    assert '<width>220</width><height>46</height><font>font18</font>' in music
    for control, left, label in ((110, 540, "Albums"), (111, 770, "Artists"),
                                 (112, 1000, "Songs"), (113, 1230, "Playlists"),
                                 (114, 1460, "Genres")):
        assert f'id="{control}"><left>{left}</left>' in music
        assert f'<label>{label}</label>' in music
    assert 'id="139"' in music and '<label>Search</label>' in music
    assert 'AsterClockPill' in music and 'AsterNavigationRail' in music
    assert '<top>86</top><width>200</width><height>4</height>' not in music

    # Requests has a direct artwork detail stage, direct multi-season toggles and one action.
    assert 'AsterSeerr.DetailsActive' in requests
    assert 'id="40"' in requests and 'AsterSeerr.Command,season' in requests
    assert 'id="50"' in requests and 'AsterSeerr.Command,request' in requests
    assert 'id="41"' not in requests and '<label>Select season</label>' not in requests
    assert 'id="30"' in requests and 'AsterSeerr.Command,details' in requests
    assert 'id="50"' not in acquisition and 'AsterAcquisition.Command,action' in acquisition
    assert '11132: frozenset((30, 40))' in dispatcher
    assert '11133: frozenset((30,))' in dispatcher
    assert "command == 'season'" in seerr and 'seasons.selectItem(position)' in seerr

    # Previously accepted regressions remain pinned.
    assert 'plugin://plugin.video.youtube/special/recommendations' in youtube
    assert 'plugin://plugin.video.youtube/special/playlist/WL' in youtube
    assert 'target=self.selection.season+1' in series
    assert "item.setProperty('Watched','true' if row.watched else 'false')" in series
    assert '<defaultcontrol always="true">300</defaultcontrol>' in series_xml
    assert '$INFO[System.Time(HH:mm)]' in series_xml
    assert 'progress-enabled.json' in books_service
    assert 'podcast_resumes' in books_bridge and 'Resume · ' in books_bridge
    assert 'sentence-sample-index' in publication and 'word-sample-index' not in publication

    promoter_text = promoter.decode()
    for guard in ('AsterTVProd', 'require_idle()', 'credentials_or_addon_data_touched',
                  'audio_settings_before', 'restore_audio_settings(saved_audio)',
                  'Settings.SetSettingValue', 'verify_installed(rows)', 'systemctl',
                  'CHECKPOINT', 'Path("/storage/.aster-recovery-required")'):
        assert guard in promoter_text
    assert 'addon_data' in promoter_text and 'SPLASH_SHA' in promoter_text

subprocess.run([sys.executable, "-m", "py_compile",
                str(ROOT / "reconciliation/promote_v207_to_production.py")], check=True)
print("AsterTV v2.0.7 release gate passed: 577 files, XML/Python, routes, splash and rollback verified")
