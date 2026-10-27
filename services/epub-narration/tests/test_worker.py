from pathlib import Path
from contextlib import closing
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).parents[1]))

from epub_narration import COMPILER_CONTRACT
from epub_narration.monitor import reconcile_catalogue
from epub_narration.publication import sha256_file
from epub_narration.state import QueueStore
from epub_narration.worker import WorkerConfig, run_once


def make_library(root: Path, text: str = "Synthetic chapter for private compiler testing."):
    library = root / "library"
    book = library / "Synthetic"
    book.mkdir(parents=True)
    epub = book / "book.epub"
    with zipfile.ZipFile(epub, "w") as archive:
        archive.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="content.opf"/></rootfiles></container>')
        archive.writestr("content.opf", '<package><manifest><item id="c1" href="chapter.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="c1"/></spine></package>')
        archive.writestr("chapter.xhtml", f"<html><body><p>{text}</p></body></html>")
    database = library / "metadata.db"
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("CREATE TABLE books(id INTEGER PRIMARY KEY,path TEXT)")
        connection.execute("CREATE TABLE data(id INTEGER PRIMARY KEY,book INTEGER,format TEXT,name TEXT)")
        connection.execute("INSERT INTO books VALUES(1,'Synthetic')")
        connection.execute("INSERT INTO data VALUES(1,1,'EPUB','book')")
    return library, database, epub


class FakeRenderer:
    def __init__(self, **_kwargs):
        pass

    def render(self, chapters, staging):
        chapter = staging / "chapters" / "0001.opus"
        timing = staging / "timing" / "0001.json"
        chapter.parent.mkdir(parents=True)
        timing.parent.mkdir(parents=True)
        chapter.write_bytes(b"synthetic-opus")
        timing.write_text(json.dumps({"schema": 1, "count": len(chapters)}))
        return [
            {"path": str(path.relative_to(staging)), "bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in (chapter, timing)
        ]

    def close(self):
        pass


class WorkerTests(unittest.TestCase):
    def config(self, root, library, database, **changes):
        values = dict(
            database=database,
            library_root=library,
            data_root=root / "reader",
            model=root / "model",
            voices=root / "voices",
            cleanup=root / "cleanup",
            minimum_free_bytes=0,
        )
        values.update(changes)
        return WorkerConfig(**values)

    def test_monitor_and_worker_publish_without_content_in_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library, database, _epub = make_library(root)
            config = self.config(root, library, database)
            monitored = reconcile_catalogue(
                database=database,
                library_root=library,
                state_root=config.state_root,
                compiler_contract=COMPILER_CONTRACT,
            )
            self.assertEqual((1, 1), (monitored["source_count"], monitored["queued_new_count"]))
            self.assertNotIn("Synthetic", json.dumps(monitored))
            result = run_once(config, renderer_factory=FakeRenderer)
            self.assertEqual("healthy", result["state"])
            pointer = json.loads((config.data_root / "ready" / "1.json").read_text())
            self.assertTrue((config.data_root / pointer["generation"] / "manifest.json").is_file())
            self.assertNotIn("Synthetic", (config.state_root / "worker-status.json").read_text())

    def test_source_change_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library, database, epub = make_library(root)
            config = self.config(root, library, database)
            reconcile_catalogue(database=database, library_root=library, state_root=config.state_root, compiler_contract=COMPILER_CONTRACT)
            with epub.open("ab") as handle:
                handle.write(b"changed")
            result = run_once(config, renderer_factory=FakeRenderer)
            self.assertEqual("failed", result["state"])
            self.assertFalse((config.data_root / "ready" / "1.json").exists())

    def test_quota_gate_fails_before_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            library, database, _epub = make_library(root)
            config = self.config(root, library, database, minimum_free_bytes=2**63)
            reconcile_catalogue(database=database, library_root=library, state_root=config.state_root, compiler_contract=COMPILER_CONTRACT)
            result = run_once(config, renderer_factory=FakeRenderer)
            self.assertEqual("failed", result["state"])
            store = QueueStore(config.state_root / "queue.db")
            with closing(sqlite3.connect(store.path)) as connection, connection:
                failure = connection.execute("SELECT failure_code FROM generations").fetchone()[0]
            self.assertEqual("quota", failure)


if __name__ == "__main__":
    unittest.main()
