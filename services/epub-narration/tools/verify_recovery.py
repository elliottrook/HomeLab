#!/usr/bin/env python3
"""Regenerate one synthetic ready generation in an isolated temporary root."""

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import zipfile

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from epub_narration import COMPILER_CONTRACT
from epub_narration.aster_books import load_ready_book
from epub_narration.monitor import reconcile_catalogue
from epub_narration.publication import sha256_file
from epub_narration.worker import WorkerConfig, run_once


class RecoveryRenderer:
    def __init__(self, **_ignored):
        pass

    def close(self):
        pass

    def render(self, chapters, staging):
        files = []
        for chapter in chapters:
            text = chapter.text
            stem = f"{chapter.index:04d}"
            boundary = text.index(".") + 1
            spans = ((0, boundary), (boundary + 1, len(text)))
            cues = [{
                "source_start": start, "source_end": end,
                "start_sample": offset * 24_000, "end_sample": (offset + 1) * 24_000,
                "spoken_sha256": hashlib.sha256(text[start:end].encode()).hexdigest(),
            } for offset, (start, end) in enumerate(spans)]
            digest = hashlib.sha256(text.encode()).hexdigest()
            payloads = {
                f"chapters/{stem}.opus": b"OggS isolated synthetic recovery",
                f"timing/{stem}.json": json.dumps({
                    "schema": 1, "timing_level": "sentence-sample-index", "sample_rate": 24_000,
                    "total_samples": 48_000, "cleaned_text_sha256": digest, "cues": cues,
                }, sort_keys=True, separators=(",", ":")).encode(),
                f"content/{stem}.json": json.dumps({
                    "schema": 1, "chapter": chapter.index, "text": text, "text_sha256": digest,
                }, sort_keys=True, separators=(",", ":")).encode(),
            }
            for relative, payload in payloads.items():
                path = staging / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                files.append({"path": relative, "bytes": len(payload), "sha256": sha256_file(path)})
        return files


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="epub-recovery-") as temporary:
        root = Path(temporary)
        library = root / "library"
        book = library / "Synthetic"
        book.mkdir(parents=True)
        epub = book / "book.epub"
        with zipfile.ZipFile(epub, "w") as archive:
            archive.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="content.opf"/></rootfiles></container>')
            archive.writestr("content.opf", '<package><manifest><item id="c1" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>')
            archive.writestr("chapter.xhtml", "<html><body><p>Recovery begins. Recovery completes.</p></body></html>")
        database = library / "metadata.db"
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.execute("CREATE TABLE books(id INTEGER PRIMARY KEY,path TEXT)")
            connection.execute("CREATE TABLE data(id INTEGER PRIMARY KEY,book INTEGER,format TEXT,name TEXT)")
            connection.execute("INSERT INTO books VALUES(1,'Synthetic')")
            connection.execute("INSERT INTO data VALUES(1,1,'EPUB','book')")
        data = root / "reader"
        reconcile_catalogue(database=database, library_root=library,
                            state_root=data / "state", compiler_contract=COMPILER_CONTRACT)
        result = run_once(WorkerConfig(database=database, library_root=library, data_root=data,
                                       model=root / "model", voices=root / "voices",
                                       cleanup=root / "cleanup", minimum_free_bytes=0),
                          renderer_factory=RecoveryRenderer)
        if result["state"] != "healthy":
            raise ValueError("recovery-worker")
        restored = load_ready_book(data, 1)
        with closing(sqlite3.connect(data / "state/queue.db")) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("recovery-state-integrity")
        print(json.dumps({"state": "passed", "ready": 1, "chapters": len(restored.chapters),
                          "isolated": True, "synthetic": True}, sort_keys=True))


if __name__ == "__main__":
    main()
