from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content import ContentError, ContentRecord
from store import ContentStore
from template_candidate import BANNER, build_template_candidate


class TemplateCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = ContentStore(self.root / "content.db")
        self.imports = self.root / "imports"
        self.template = self.root / "template"
        self.template.mkdir()
        (self.template / "styles.css").write_text("body{}")
        (self.template / "script.js").write_text("")
        for name in ("index", "landscapes", "flora", "contrasts", "people"):
            cards = '<article class="work"><button><img></button><div class="work-meta"><h3></h3></div><div class="piece-story"></div></article>' if name != "index" else '<section class="hero"><img></section><section class="featured-story"><h2></h2><div class="piece-story"></div></section>'
            (self.template / f"{name}.html").write_text(f"<html><head></head><body class=\"collection-page\">{cards}</body></html>")

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def seed(self, content_id: str, collection: str = "landscapes") -> dict:
        payload = content_id.encode()
        digest = sha256(payload).hexdigest()
        target = self.imports / "contrast" / content_id
        target.mkdir(parents=True)
        (target / f"{digest}.jpg").write_bytes(payload)
        base = dict(id=content_id, site="contrast", asset_path=f"imports/contrast/{content_id}/{digest}.jpg", image_sha256=digest, collection=collection, title="Baseline", alt_text="Alt", story=" ".join(["story"]*45), full_story="", story_mode="factual", orientation="landscape", focal_point="50% 50%", rights_status="verified", consent_status="not-applicable", credit="Jason", sample=False)
        self.store.save(ContentRecord.from_dict(base))
        return base

    def prepare(self, *content_ids: str) -> None:
        records = [self.seed(content_id) for content_id in content_ids]
        self.store.start_refresh("contrast", "Template edition")
        for base in records:
            self.store.save(ContentRecord.from_dict({**base, "title": "Replacement"}))
            self.store.approve("contrast", base["id"], "jason")

    def test_preserves_template_and_injects_private_binding(self):
        self.prepare("slot-one")
        destination = self.root / "candidate"
        build_template_candidate(self.store, self.imports, "contrast", self.template, destination)
        self.assertIn(BANNER, (destination / "index.html").read_text())
        self.assertIn("candidate-bindings.js", (destination / "landscapes.html").read_text())
        self.assertIn("Replacement", (destination / "candidate-bindings.js").read_text())
        self.assertTrue((destination / "MANIFEST.sha256").is_file())

    def test_refuses_more_records_than_template_capacity(self):
        self.prepare("slot-one", "slot-two")
        with self.assertRaisesRegex(ContentError, "capacity"):
            build_template_candidate(self.store, self.imports, "contrast", self.template, self.root / "too-many")
        self.assertFalse((self.root / "too-many").exists())


if __name__ == "__main__":
    unittest.main()
