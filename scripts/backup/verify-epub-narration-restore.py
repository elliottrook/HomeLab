#!/usr/bin/env python3
"""Verify an isolated, media-free EPUB narration state restore."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tarfile
import tempfile


QUEUE = "configuration/epub-narration/state/queue.db"
MANIFEST = "configuration/manifest.json"
MEDIA_PARTS = {"chapters", "content", "timing", "work", "failed"}


def verify(archive_path: Path) -> dict:
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        names = {member.name for member in members}
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
            raise ValueError("restore-archive-path")
        if QUEUE not in names or MANIFEST not in names:
            raise ValueError("restore-state-missing")
        epub_names = {name for name in names if name.startswith("configuration/epub-narration/")}
        if any(MEDIA_PARTS.intersection(PurePosixPath(name).parts) for name in epub_names):
            raise ValueError("restore-media-present")
        manifest_file = archive.extractfile(MANIFEST)
        queue_file = archive.extractfile(QUEUE)
        if manifest_file is None or queue_file is None:
            raise ValueError("restore-state-type")
        manifest = json.load(manifest_file)
        queue_bytes = queue_file.read(64 * 1024 * 1024 + 1)
        if len(queue_bytes) > 64 * 1024 * 1024 or manifest.get("media_included") is not False:
            raise ValueError("restore-state-boundary")
        wanted = manifest.get("files", {}).get("epub-narration/state/queue.db")
        if wanted != hashlib.sha256(queue_bytes).hexdigest():
            raise ValueError("restore-state-hash")
        with tempfile.TemporaryDirectory(prefix="epub-state-restore-") as temporary:
            restored = Path(temporary) / "queue.db"
            restored.write_bytes(queue_bytes)
            restored.chmod(0o600)
            with sqlite3.connect(restored) as connection:
                if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("restore-state-integrity")
                counts = {state: count for state, count in connection.execute(
                    "SELECT state,COUNT(*) FROM generations GROUP BY state"
                )}
            if restored.stat().st_mode & 0o077:
                raise ValueError("restore-state-mode")
        ready = sum(name.startswith("configuration/epub-narration/ready/") for name in names)
        immutable = sum(name.endswith("/manifest.json") and name.startswith(
            "configuration/epub-narration/generations/") for name in names)
        return {"state": "passed", "isolated": True, "media_included": False,
                "queue_records": sum(counts.values()), "ready_pointers": ready,
                "generation_manifests": immutable}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    result = verify(parser.parse_args().archive)
    print(json.dumps(result, sort_keys=True))
