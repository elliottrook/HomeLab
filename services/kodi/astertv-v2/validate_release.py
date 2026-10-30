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
ARCHIVE = REPO / "services/kodi/dist/astertv-v2-lab-reconciled-2026-10-30-r8.tar.gz"
SIDECAR = ARCHIVE.with_suffix(ARCHIVE.suffix + ".sha256")
EXPECTED_RELEASE = "astertv-v2.0.6-lab-repair-complete-2026-10-30-r8"


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
assert packaged == manifest

print(f"AsterTV v2 release gate passed: {len(manifest['files'])} payload files and r8 archive verified")
