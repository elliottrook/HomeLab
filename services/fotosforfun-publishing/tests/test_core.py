from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model import ContentError, Photo
from renderer import PLACEHOLDER_NOTICE, render
from release import activate_release, prepare_release, verify_manifest
from store import CatalogueStore


def photo(photo_id: str = "quiet-dahlia", *, order: int = 10,
          sample: bool = False, retired: bool = False) -> Photo:
    digest = sha256(photo_id.encode()).hexdigest()
    return Photo(photo_id, "Quiet dahlia", "flowers", "An orange dahlia in soft light",
                 f"imports/fotosforfun/{photo_id}/{digest}.jpg", digest, 1200, 800,
                 order, "owned", retired=retired, sample=sample)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = CatalogueStore(self.root / "state" / "catalogue.db")

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def test_state_is_private_and_append_order_is_stable(self):
        first = photo("first-photo", order=20)
        second = photo("second-photo", order=10)
        self.assertEqual(self.store.save(first, "alisa"), 1)
        self.assertEqual(self.store.save(second, "alisa"), 1)
        self.store.approve(first.id, "alisa")
        self.store.approve(second.id, "alisa")
        self.assertEqual([item[0].id for item in self.store.publishable()],
                         [second.id, first.id])
        self.assertEqual((self.root / "state").stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.root / "state" / "catalogue.db").stat().st_mode & 0o777, 0o600)

    def test_edit_invalidates_approval_and_sample_fails_closed(self):
        original = photo()
        self.store.save(original, "alisa")
        self.store.approve(original.id, "alisa")
        self.assertIsNotNone(self.store.current_approval(original.id))
        self.store.save(replace(original, title="Changed title"), "alisa")
        self.assertIsNone(self.store.current_approval(original.id))
        sample = photo("sample-photo", sample=True)
        self.store.save(sample, "alisa")
        with self.assertRaisesRegex(ContentError, "sample"):
            self.store.approve(sample.id, "alisa")
        with self.assertRaisesRegex(ContentError, "Changed|awaiting approval"):
            self.store.publication_snapshot()

    def test_publication_snapshot_never_silently_drops_active_items(self):
        approved = photo("approved-photo", order=20)
        pending = photo("pending-photo", order=10)
        self.store.save(approved, "alisa")
        self.store.approve(approved.id, "alisa")
        self.store.save(pending, "alisa")
        with self.assertRaisesRegex(ContentError, "pending-photo: awaiting approval"):
            self.store.publication_snapshot()
        self.store.approve(pending.id, "alisa")
        self.assertEqual([item[0].id for item in self.store.publication_snapshot()],
                         [pending.id, approved.id])

    def test_retirement_is_confirmed_versioned_and_reversible(self):
        item = photo()
        self.store.save(item, "alisa")
        with self.assertRaisesRegex(ContentError, "confirmation"):
            self.store.set_retired(item.id, True, "alisa")
        self.assertEqual(self.store.set_retired(item.id, True, "alisa", "RETIRE PHOTO"), 2)
        self.assertEqual(self.store.publishable(), [])
        self.assertEqual(self.store.set_retired(item.id, False, "alisa"), 3)
        self.assertFalse(self.store.latest(item.id)[0].retired)

    def test_cross_site_paths_and_bad_rights_are_rejected(self):
        with self.assertRaisesRegex(ContentError, "outside"):
            replace(photo(), asset_path="imports/contrast/private.jpg").validate()
        with self.assertRaisesRegex(ContentError, "rights note"):
            replace(photo(), rights="licensed").validate()


class RenderReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.template = self.root / "template"
        (self.template / "assets").mkdir(parents=True)
        (self.template / "index.html").write_text(
            '<html><body><main id="gallery"></main><a href="mailto:hello@fotosforfun.com">'
            'hello@fotosforfun.com</a><dialog id="viewer"><button id="close"></button>'
            '<button id="previous"></button><img id="viewer-image"><button id="next"></button>'
            '<span id="viewer-position"></span><h2 id="viewer-title"></h2>'
            '<p id="viewer-category"></p><p id="viewer-credit"></p></dialog>'
            '<span id="count"></span><script src="gallery.js"></script></body></html>')
        (self.template / "gallery.js").write_text("unsafe old renderer")
        self.imports = self.root / "imports"

    def tearDown(self):
        self.temporary.cleanup()

    def install_image(self, item: Photo) -> None:
        target = self.imports / item.asset_path.removeprefix("imports/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(item.id.encode())

    def test_safe_candidate_preserves_template_and_corrects_mail(self):
        item = photo()
        self.install_image(item)
        candidate = self.root / "candidate"
        result = render(self.template, candidate, [item], self.imports)
        html = (candidate / "index.html").read_text()
        script = (candidate / "gallery.js").read_text()
        data = json.loads((candidate / "gallery-data.json").read_text())
        self.assertIn("hello@fotosforfun.ca", html)
        self.assertNotIn("hello@fotosforfun.com", html)
        self.assertNotIn("innerHTML", script)
        self.assertIn("textContent", script)
        self.assertEqual(data[0]["title"], item.title)
        self.assertEqual(result["photoCount"], 1)
        self.assertEqual(verify_manifest(candidate), result["manifestSha256"])

    def test_changed_image_and_sample_publication_fail_closed(self):
        item = photo()
        self.install_image(item)
        target = self.imports / item.asset_path.removeprefix("imports/")
        target.write_bytes(b"changed")
        with self.assertRaisesRegex(ContentError, "checksum changed"):
            render(self.template, self.root / "bad", [item], self.imports)
        sample = photo("sample-photo", sample=True)
        self.install_image(sample)
        with self.assertRaisesRegex(ContentError, "sample"):
            render(self.template, self.root / "sample-rejected", [sample], self.imports)
        preview = self.root / "sample-preview"
        render(self.template, preview, [sample], self.imports, allow_samples=True)
        self.assertIn(PLACEHOLDER_NOTICE, (preview / "index.html").read_text())
        with self.assertRaisesRegex(ContentError, "samples"):
            prepare_release(preview, self.root / "releases")

    def test_release_is_immutable_and_switch_returns_rollback_target(self):
        item = photo()
        self.install_image(item)
        candidate = self.root / "candidate"
        render(self.template, candidate, [item], self.imports)
        releases = self.root / "releases"
        releases.mkdir()
        result = prepare_release(candidate, releases)
        self.assertEqual(result, prepare_release(candidate, releases))
        release = releases / result["releaseId"]
        current = self.root / "current"
        self.assertIsNone(activate_release(release, releases, current))
        old = releases / "fotosforfun-old-old"
        old.mkdir()
        (old / "index.html").write_text("old")
        from renderer import write_manifest
        write_manifest(old)
        current.unlink()
        current.symlink_to(old)
        previous = activate_release(release, releases, current)
        self.assertEqual(Path(previous), old)
        self.assertEqual(current.resolve(), release.resolve())


if __name__ == "__main__":
    unittest.main()
