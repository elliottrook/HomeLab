from hashlib import sha256
from io import BytesIO
from pathlib import Path
import os
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import origin_receiver
from origin_receiver import ReceiverError, activate, extract_archive, verify


def write_release(root: Path, text: str = "release") -> str:
    root.mkdir(parents=True)
    (root / "index.html").write_text(text)
    digest = sha256((root / "index.html").read_bytes()).hexdigest()
    (root / "MANIFEST.sha256").write_text(f"{digest}  ./index.html\n")
    return sha256((root / "MANIFEST.sha256").read_bytes()).hexdigest()


class ReceiverTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.original_root = origin_receiver.ROOT
        origin_receiver.ROOT = self.root

    def tearDown(self):
        origin_receiver.ROOT = self.original_root
        self.temporary.cleanup()

    def test_atomic_activation_tracks_previous_per_site(self):
        releases = self.root / "contrast" / "releases"
        old = releases / "contrast-e1-111111111111"
        new = releases / "contrast-e2-222222222222"
        write_release(old, "old")
        digest = write_release(new, "new")
        site = self.root / "contrast"
        (site / "current").symlink_to(old)
        result = activate("contrast", new.name, digest)
        self.assertEqual(Path(result["previous"]), old)
        self.assertEqual((site / "current").resolve(), new.resolve())
        self.assertEqual((site / "previous").resolve(), old.resolve())

    def test_rejects_markers_tampering_and_cross_site_id(self):
        release = self.root / "contrast" / "releases" / "contrast-e1-111111111111"
        write_release(release, "PRIVATE CANDIDATE")
        with self.assertRaisesRegex(ReceiverError, "marker"):
            verify(release)
        write_release(self.root / "closet" / "releases" / "closet-e1-222222222222")
        with self.assertRaisesRegex(ReceiverError, "invalid release id"):
            activate("contrast", "closet-e1-222222222222", "0" * 64)

    def test_archive_policy_rejects_symlinks_and_traversal(self):
        for name, configure in [
            ("link", lambda info: setattr(info, "type", tarfile.SYMTYPE)),
            ("../escape", lambda info: None),
        ]:
            stream = BytesIO()
            with tarfile.open(fileobj=stream, mode="w") as archive:
                info = tarfile.TarInfo(name)
                configure(info)
                if info.type == tarfile.REGTYPE:
                    info.size = 1
                    archive.addfile(info, BytesIO(b"x"))
                else:
                    info.linkname = "index.html"
                    archive.addfile(info)
            stream.seek(0)
            with self.assertRaisesRegex(ReceiverError, "unsafe member"):
                extract_archive(stream, self.root / f"extract-{name.replace('/', '-')}")


if __name__ == "__main__":
    unittest.main()
