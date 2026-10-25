import gzip
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from build_fixed_doctor_staging_archive import archive_bytes, members, write_exclusive
from validate_fixed_doctor_bundle import MANIFEST


class StagingArchiveTest(unittest.TestCase):
    def test_archive_is_deterministic_private_and_complete(self):
        first = archive_bytes()
        self.assertEqual(first, archive_bytes())
        with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as archive:
            names = tuple(member.name for member in archive.getmembers())
            self.assertEqual(names, members())
            self.assertTrue(all(member.isfile() and member.mode == 0o600 for member in archive.getmembers()))
            self.assertTrue(all(member.uid == 0 and member.gid == 0 for member in archive.getmembers()))
        manifest = json.loads(MANIFEST.read_text())
        for entry in manifest["entries"]:
            self.assertIn(entry["source"], names)

    def test_writer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "candidate.tar.gz"
            write_exclusive(path, b"first")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                write_exclusive(path, b"second")
            self.assertEqual(path.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
