from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from editor import EditorApplication, HttpBoundary
from model import ContentError, Photo


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.template = self.root / "template"
        (self.template / "assets").mkdir(parents=True)
        (self.template / "index.html").write_text(
            '<html><body><main id="gallery"></main><span id="count"></span>'
            '<dialog id="viewer"><button id="close"></button><button id="previous"></button>'
            '<img id="viewer-image"><button id="next"></button><span id="viewer-position"></span>'
            '<h2 id="viewer-title"></h2><p id="viewer-category"></p><p id="viewer-credit"></p>'
            '</dialog><script src="gallery.js"></script></body></html>')
        (self.template / "gallery.js").write_text("old")
        self.web = self.root / "web"
        self.web.mkdir()
        (self.web / "index.html").write_text("desk")
        self.app = EditorApplication(self.root / "state", self.template, magick="/missing")
        self.boundary = HttpBoundary(self.app, self.web)
        digest = sha256(b"image").hexdigest()
        target = self.app.imports_root / "fotosforfun" / "first-photo" / f"{digest}.jpg"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"image")
        self.photo = Photo("first-photo", "First photo", "flowers", "A flower",
                           f"imports/fotosforfun/first-photo/{digest}.jpg", digest,
                           1200, 800, 10, "owned", sample=True)
        self.app.store.save(self.photo, "alisa")

    def tearDown(self):
        self.app.close()
        self.temporary.cleanup()

    def test_edit_invalidates_approval_and_retirement_is_reversible(self):
        self.assertFalse(self.app.catalogue()[0]["approved"])
        with self.assertRaisesRegex(ContentError, "sample"):
            self.app.approve("first-photo", "alisa")
        self.assertEqual(self.app.edit("first-photo", {"title": "A changed title"}, "alisa")["version"], 2)
        self.app.retire("first-photo", True, "alisa")
        self.assertTrue(self.app.catalogue()[0]["retired"])
        self.app.retire("first-photo", False, "alisa")
        self.assertFalse(self.app.catalogue()[0]["retired"])

    def test_preview_is_sample_capable_and_manifested(self):
        result = self.app.build_preview()
        self.assertEqual(result["photoCount"], 1)
        self.assertTrue(result["samples"])
        self.assertTrue((self.app.preview_root / "candidate" / "MANIFEST.sha256").is_file())
        status, mime, body = self.boundary.dispatch("GET", "/preview/gallery-data.json")
        self.assertEqual((status, mime), (200, "application/json"))
        self.assertEqual(json.loads(body)[0]["title"], "First photo")

    def test_http_has_no_publish_action_and_rejects_traversal(self):
        status, _, body = self.boundary.dispatch("POST", "/api/publish", b"{}", "alisa")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)["error"], "Not found")
        status, _, _ = self.boundary.dispatch("GET", "/preview/../catalogue.db")
        self.assertEqual(status, 400)
        status, _, body = self.boundary.dispatch("GET", "/api/photos")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["photos"][0]["id"], "first-photo")

    def test_invalid_actor_fails_closed(self):
        status, _, body = self.boundary.dispatch(
            "POST", "/api/photos/first-photo", json.dumps({"title": "x"}).encode(), "bad\nactor")
        self.assertEqual(status, 400)
        self.assertIn("actor", json.loads(body)["error"])


if __name__ == "__main__":
    unittest.main()
