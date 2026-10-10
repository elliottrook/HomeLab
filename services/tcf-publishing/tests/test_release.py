from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content import ContentError
from release import activate_release, prepare_release, verify_manifest
from template_candidate import BANNER, BANNER_STYLE


def write_manifest(root: Path) -> None:
    entries = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()
                       and item.name != "MANIFEST.sha256"):
        entries.append(f"{sha256(path.read_bytes()).hexdigest()}  ./{path.relative_to(root).as_posix()}")
    (root / "MANIFEST.sha256").write_text("\n".join(entries) + "\n")


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def candidate(self) -> Path:
        candidate = self.root / "candidate"
        candidate.mkdir()
        (candidate / "index.html").write_text(
            f"<html><head>{BANNER_STYLE}</head><body>{BANNER}finished site</body></html>")
        (candidate / "styles.css").write_text("body{}")
        (candidate / "candidate.json").write_text(json.dumps({
            "site": "contrast", "edition_id": 4, "slots": [], "content": []}))
        write_manifest(candidate)
        return candidate

    def test_prepares_public_release_and_atomic_switch_with_rollback_target(self):
        candidate = self.candidate()
        releases = self.root / "releases"
        releases.mkdir()
        first = releases / "contrast-e3-old"
        first.mkdir()
        (first / "index.html").write_text("old")
        write_manifest(first)
        current = self.root / "current"
        current.symlink_to(first)
        release = releases / "contrast-e4-new"
        result = prepare_release(candidate, release, "contrast")
        self.assertNotIn("PRIVATE CANDIDATE", (release / "index.html").read_text())
        self.assertFalse((release / "candidate.json").exists())
        previous = activate_release(release, releases, current)
        self.assertEqual(Path(previous), first)
        self.assertEqual(current.resolve(), release.resolve())
        self.assertEqual(result["site"], "contrast")

    def test_rejects_changed_missing_extra_and_wrong_site(self):
        candidate = self.candidate()
        (candidate / "styles.css").write_text("changed")
        with self.assertRaisesRegex(ContentError, "checksum"):
            verify_manifest(candidate)
        write_manifest(candidate)
        with self.assertRaisesRegex(ContentError, "site or edition"):
            prepare_release(candidate, self.root / "wrong", "closet")
        (candidate / "extra.txt").write_text("extra")
        with self.assertRaisesRegex(ContentError, "do not match"):
            verify_manifest(candidate)


if __name__ == "__main__":
    unittest.main()
