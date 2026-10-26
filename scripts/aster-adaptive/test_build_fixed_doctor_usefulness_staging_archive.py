import hashlib
import tarfile
import tempfile
import unittest
from pathlib import Path

import build_fixed_doctor_usefulness_staging_archive as builder


ROOT = Path(__file__).parent


class BuildFixedDoctorUsefulnessStagingArchiveTests(unittest.TestCase):
    def test_archive_is_deterministic_exact_and_root_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.tar.gz"
            second = Path(temporary) / "second.tar.gz"
            builder.build(ROOT, first)
            builder.build(ROOT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with tarfile.open(first, "r:gz") as archive:
                members = archive.getmembers()
                self.assertEqual(sorted(builder.SOURCES), [item.name for item in members])
                for member in members:
                    self.assertTrue(member.isfile())
                    self.assertEqual((0, 0, 0o600, 0), (
                        member.uid, member.gid, member.mode, member.mtime
                    ))
                    source = ROOT / builder.SOURCES[member.name]
                    extracted = archive.extractfile(member)
                    self.assertIsNotNone(extracted)
                    self.assertEqual(
                        hashlib.sha256(source.read_bytes()).hexdigest(),
                        hashlib.sha256(extracted.read()).hexdigest(),
                    )

    def test_existing_output_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet.tar.gz"
            output.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                builder.build(ROOT, output)
            self.assertEqual(b"keep", output.read_bytes())


if __name__ == "__main__":
    unittest.main()
