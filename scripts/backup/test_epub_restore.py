from io import BytesIO
from pathlib import Path
import hashlib
import importlib.util
import json
import sqlite3
import tarfile
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("verify-epub-narration-restore.py")
SPEC = importlib.util.spec_from_file_location("verify_epub_restore", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class EpubRestoreTests(unittest.TestCase):
    def archive(self, root: Path, include_media=False):
        queue = root / "queue.db"
        with sqlite3.connect(queue) as connection:
            connection.execute("CREATE TABLE generations(state TEXT)")
            connection.execute("INSERT INTO generations VALUES('queued')")
        payload = queue.read_bytes()
        manifest = json.dumps({"media_included": False, "files": {
            "epub-narration/state/queue.db": hashlib.sha256(payload).hexdigest()
        }}).encode()
        archive = root / "configs.tar.gz"
        with tarfile.open(archive, "w:gz") as stream:
            for name, raw in ((MODULE.MANIFEST, manifest), (MODULE.QUEUE, payload)):
                info = tarfile.TarInfo(name); info.size = len(raw); stream.addfile(info, BytesIO(raw))
            if include_media:
                raw = b"private"
                info = tarfile.TarInfo("configuration/epub-narration/chapters/0001.opus")
                info.size = len(raw); stream.addfile(info, BytesIO(raw))
        return archive

    def test_isolated_restore_and_media_exclusion(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = MODULE.verify(self.archive(Path(temporary)))
            self.assertEqual(1, result["queue_records"])
            self.assertFalse(result["media_included"])

    def test_rejects_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "restore-media-present"):
                MODULE.verify(self.archive(Path(temporary), True))


if __name__ == "__main__":
    unittest.main()
