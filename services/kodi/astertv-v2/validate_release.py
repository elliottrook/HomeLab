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
ARCHIVE = REPO / "services/kodi/dist/astertv-v2-lab-reconciled-2026-10-30-r9.tar.gz"
SIDECAR = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
EXPECTED_RELEASE = "astertv-v2.0.6-lab-repair-complete-2026-10-30-r9"


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
    assert service_member is not None and bridge_member is not None and listing_member is not None
    service_source = service_member.read().decode("utf-8")
    bridge_source = bridge_member.read().decode("utf-8")
    listing_source = listing_member.read().decode("utf-8")
assert packaged == manifest
assert reader_bundle["shared_progress"] is False
assert "sentence-sample-index" in publication_source
assert "word-sample-index" not in publication_source
assert "ProgressBridge" in service_source and "progress-enabled.json" in service_source
assert "kind=='podcast'" in bridge_source and "Resume · " in bridge_source
assert "AsterBooks.Resume" in listing_source and "StartOffset" in listing_source

print(f"AsterTV v2 release gate passed: {len(manifest['files'])} payload files and r9 archive verified")
