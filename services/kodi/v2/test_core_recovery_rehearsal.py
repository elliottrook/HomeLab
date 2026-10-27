import hashlib
import tempfile
import unittest
from pathlib import Path
import zipfile

from core_recovery_rehearsal import copy_tree, extract
from release_inventory import InventoryError


class CoreRecoveryRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)

    def tearDown(self): self.temp.cleanup()

    def test_exact_archive_extracts(self):
        raw = b"safe\n"; archive = self.root / "safe.zip"
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr("addon/file.txt", raw)
        rows = [{"path": "addon/file.txt", "bytes": len(raw),
                 "sha256": hashlib.sha256(raw).hexdigest()}]
        target = self.root / "target"; extract(archive, target, rows)
        self.assertEqual((target / "addon/file.txt").read_bytes(), raw)

    def test_archive_traversal_and_source_symlink_are_refused(self):
        archive = self.root / "bad.zip"
        with zipfile.ZipFile(archive, "w") as package:
            package.writestr("../escape", b"bad")
        rows = [{"path": "../escape", "bytes": 3,
                 "sha256": hashlib.sha256(b"bad").hexdigest()}]
        with self.assertRaisesRegex(InventoryError, "archive-path"):
            extract(archive, self.root / "target", rows)
        source = self.root / "source"; source.mkdir()
        (source / "linked").symlink_to(self.root / "outside")
        with self.assertRaisesRegex(InventoryError, "linked-source"):
            copy_tree(source, self.root / "copy")


if __name__ == "__main__": unittest.main()
