import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_sa2_doctor_producer_packet import ENTRIES, ROOT, entries, packet_bytes, write_exclusive


class Sa2DoctorProducerPacketTests(unittest.TestCase):
    def test_packet_is_deterministic_flat_private_and_exact(self):
        first = packet_bytes()
        self.assertEqual(first, packet_bytes())
        with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as archive:
            members = archive.getmembers()
            self.assertEqual([name for name, _ in entries()], [item.name for item in members])
            self.assertEqual(3, len(members))
            self.assertTrue(all(item.isfile() and "/" not in item.name for item in members))
            self.assertTrue(all(item.mode == 0o600 and item.uid == 0 and item.gid == 0 for item in members))
            self.assertTrue(all(item.uname == "root" and item.gname == "root" and item.mtime == 0 for item in members))

    def test_changed_or_linked_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for expected in ENTRIES.values():
                target = root / expected["source"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / expected["source"]).read_bytes())
            first = next(iter(ENTRIES.values()))
            changed = root / first["source"]
            changed.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                entries(root)
            changed.unlink()
            changed.symlink_to(ROOT / first["source"])
            with self.assertRaises(OSError):
                entries(root)

    def test_mismatched_target_basename_fails_closed(self):
        changed = dict(ENTRIES)
        target, expected = next(iter(changed.items()))
        changed[target + ".wrong"] = changed.pop(target)
        with patch("build_sa2_doctor_producer_packet.ENTRIES", changed):
            with self.assertRaisesRegex(ValueError, "mismatched"):
                entries()

    def test_writer_is_private_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.tar.gz"
            write_exclusive(path, b"one")
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                write_exclusive(path, b"two")
            self.assertEqual(b"one", path.read_bytes())


if __name__ == "__main__":
    unittest.main()
