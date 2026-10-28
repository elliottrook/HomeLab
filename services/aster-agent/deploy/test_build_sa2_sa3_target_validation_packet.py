import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from build_sa2_sa3_target_validation_packet import ROOT, SUPPORT, TESTS, entries, packet_bytes, write_exclusive


class Sa2Sa3TargetValidationPacketTests(unittest.TestCase):
    def test_packet_is_deterministic_exact_flat_and_private(self):
        raw = packet_bytes()
        self.assertEqual(raw, packet_bytes())
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            members = archive.getmembers()
            self.assertEqual([name for name, _ in entries()], [item.name for item in members])
            self.assertEqual(17, len(members))
            self.assertEqual(["evals/sysadmin-producer-fixture.json"],
                             [item.name for item in members if "/" in item.name])
            self.assertTrue(all(item.isfile() for item in members))
            self.assertTrue(all(item.mode == 0o600 and item.uid == item.gid == 0 for item in members))

    def test_changed_or_linked_test_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for source in TESTS:
                path = root / source
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / source).read_bytes())
            for source, _expected in SUPPORT.values():
                path = root / source
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / source).read_bytes())
            # Candidate files are read by the release builder, so copy them too.
            for name, raw in __import__("build_sa2_sa3_composite_packet").entries():
                path = root / "services/aster-agent" / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            first = root / next(iter(TESTS))
            first.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                entries(root)
            first.unlink()
            first.symlink_to(ROOT / next(iter(TESTS)))
            with self.assertRaises(OSError):
                entries(root)

    def test_writer_is_private_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "validation.tar.gz"
            write_exclusive(path, b"one")
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                write_exclusive(path, b"two")


if __name__ == "__main__":
    unittest.main()
