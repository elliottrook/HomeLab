#!/usr/bin/env python3
"""Fail closed if the preserved AsterTV v2 lab release drifts."""

import hashlib
import json
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RECONCILIATION = ROOT / "reconciliation"
MANIFEST = RECONCILIATION / "manifest.json"
ARCHIVE = REPO / "services/kodi/dist/astertv-v2-lab-reconciled-2026-10-30-r13.tar.gz"
SIDECAR = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
EXPECTED_RELEASE = "astertv-v2.0.6-lab-acceptance-reconciled-2026-10-30-r13"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


manifest = json.loads(MANIFEST.read_text())
assert manifest["release"] == EXPECTED_RELEASE
assert manifest["target"] == "AsterTV lab only (192.168.1.140)"
assert manifest["production_changed"] is False

for row in manifest["files"]:
    candidate = RECONCILIATION / "payload" / row["path"]
    assert candidate.is_file(), row["path"]
    assert candidate.stat().st_size == row["bytes"], row["path"]
    assert sha256(candidate) == row["after_sha256"], row["path"]

subprocess.run([sys.executable, str(RECONCILIATION / "validate_books_music.py")], check=True)
subprocess.run([sys.executable, "-m", "py_compile",
                str(RECONCILIATION / "apply_reconciliation.py")], check=True)

sidecar_hash, sidecar_name = SIDECAR.read_text().split()
assert sidecar_name == ARCHIVE.name
assert sha256(ARCHIVE) == sidecar_hash
with tarfile.open(ARCHIVE, "r:gz") as bundle:
    member = bundle.extractfile("aster-v2-package/reconciliation/manifest.json")
    assert member is not None
    packaged = json.load(member)
    reader_bundle_member = bundle.extractfile("aster-v2-package/epub-consumer/reader/bundle.json")
    assert reader_bundle_member is not None
    reader_bundle = json.load(reader_bundle_member)
    publication_member = bundle.extractfile(
        "aster-v2-package/epub-consumer/reader/runtime/epub_narration/publication.py"
    )
    assert publication_member is not None
    publication_source = publication_member.read().decode("utf-8")
    service_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/plugin.audio.asterbooks/service.py"
    )
    bridge_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/plugin.audio.asterbooks/resources/lib/books_sync_bridge.py"
    )
    listing_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/plugin.audio.asterbooks/default.py"
    )
    series_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/script.asterruntime/aster-series-preview24/default.py"
    )
    series_xml_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/script.asterruntime/aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml"
    )
    series_manifest_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/script.asterruntime/aster-series-preview24/manifest.json"
    )
    series_wrapper_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/skin.asterhome/tools/aster_v2_series.py"
    )
    family_manifest_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/script.asterruntime/family-manifest.json"
    )
    movie_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/script.asterruntime/aster-global-search-ui22/movie.py"
    )
    home_plugin_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/plugin.video.asterhome/default.py"
    )
    requests_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/skin.asterhome/1080i/custom_1132_requests.xml"
    )
    youtube_focus_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/skin.asterhome/tools/youtube_root_focus.py"
    )
    screensaver_member = bundle.extractfile(
        "aster-v2-package/lab-addon-snapshot/screensaver.asterhome.v2lab/resources/skins/Default/1080i/AsterIdle.xml"
    )
    assert service_member is not None and bridge_member is not None and listing_member is not None
    assert all(member is not None for member in (
        series_member, series_xml_member, series_manifest_member,
        series_wrapper_member, family_manifest_member, movie_member, home_plugin_member,
        requests_member, youtube_focus_member, screensaver_member))
    service_source = service_member.read().decode("utf-8")
    bridge_source = bridge_member.read().decode("utf-8")
    listing_source = listing_member.read().decode("utf-8")
    series_source = series_member.read().decode("utf-8")
    series_xml = series_xml_member.read().decode("utf-8")
    series_manifest = json.loads(series_manifest_member.read())
    series_wrapper = series_wrapper_member.read().decode("utf-8")
    family_manifest = json.loads(family_manifest_member.read())
    movie_source = movie_member.read().decode("utf-8")
    home_plugin_source = home_plugin_member.read().decode("utf-8")
    requests_xml = requests_member.read().decode("utf-8")
    youtube_focus_source = youtube_focus_member.read().decode("utf-8")
    screensaver_xml = screensaver_member.read().decode("utf-8")
assert packaged == manifest
assert reader_bundle["shared_progress"] is False
assert "sentence-sample-index" in publication_source
assert "word-sample-index" not in publication_source
assert "ProgressBridge" in service_source and "progress-enabled.json" in service_source
assert "podcast_resumes" in bridge_source and "Resume · " in bridge_source
assert "AsterBooks.Resume" in listing_source and "StartOffset" in listing_source
assert "target=self.selection.season+1" in series_source
assert "item.setProperty('Watched','true' if row.watched else 'false')" in series_source
assert "preview-window-identity-timeout" in series_source
assert "window.identity=current" in series_source
assert "self.setProperty('Series.SeasonIndex',str(self.selection.season))" in series_source
assert "if self.identity is not None:self.setFocusId" in series_source
assert '<defaultcontrol always="true">300</defaultcontrol>' in series_xml
assert 'colordiffuse="b8000000"' in series_xml
assert 'id="201"' in series_xml and 'colordiffuse="ff005c46"' in series_xml
assert "AsterMovieRails: controls cast=" in movie_source
assert "command=='related'" in movie_source and "VideoLibrary.GetMovies" in movie_source
assert "row['kind'] == 'movie'" in home_plugin_source and "setDbId(row['id'])" in home_plugin_source
assert 'railfocus" value="9009"' in requests_xml
assert 'id="40"><left>1210</left><top>190</top><width>570</width><height>300</height>' in requests_xml
assert 'id="41"><left>1210</left><top>505</top><width>570</width><height>56</height>' in requests_xml
assert 'id="50"><left>1210</left><top>615</top><width>570</width><height>64</height>' in requests_xml
assert 'id="30"><left>110</left><top>715</top>' in requests_xml
series_component_bytes = (json.dumps(series_manifest, indent=2, sort_keys=True) + "\n").encode()
series_component_sha = __import__("hashlib").sha256(series_component_bytes).hexdigest()
assert f"MANIFEST_SHA='{series_component_sha}'" in series_wrapper
assert family_manifest["components"]["aster-series-preview24"]["manifest_sha256"] == series_component_sha
assert "if focused in ROOT_CONTROLS" in youtube_focus_source
assert "<backgroundcolor>ff000000</backgroundcolor>" in screensaver_xml

print(f"AsterTV v2 release gate passed: {len(manifest['files'])} payload files and r13 archive verified")
