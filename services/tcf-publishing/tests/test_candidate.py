from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from candidate import build_candidate
from content import ContentError, ContentRecord
from store import ContentStore


def record(content_id: str, digest: str, **changes) -> ContentRecord:
    value = dict(
        id=content_id, site="contrast",
        asset_path=f"imports/contrast/{content_id}/{digest}.jpg",
        image_sha256=digest, collection="landscapes", title="Replacement",
        alt_text="A replacement photograph", story=" ".join(["story"] * 45),
        full_story="", story_mode="factual", orientation="landscape",
        focal_point="50% 50%", rights_status="verified",
        consent_status="not-applicable", credit="Jason Elliott", sample=False,
        annotation_text="New work", annotation_x=80, annotation_y=38,
    )
    value.update(changes)
    return ContentRecord.from_dict(value)


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = ContentStore(self.root / "content.db")
        self.imports = self.root / "imports"

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def add_image(self, content_id: str, payload: bytes = b"approved-image") -> str:
        digest = sha256(payload).hexdigest()
        target = self.imports / "contrast" / content_id
        target.mkdir(parents=True)
        (target / f"{digest}.jpg").write_bytes(payload)
        return digest

    def test_builds_only_complete_hash_bound_candidate(self):
        digest = self.add_image("slot-one")
        self.store.save(record("slot-one", digest, title="Baseline"))
        self.store.start_refresh("contrast", "Fortnight 1")
        self.store.save(record("slot-one", digest, title="Fresh edition"))
        self.store.approve("contrast", "slot-one", "jason")
        destination = self.root / "candidate"
        manifest = build_candidate(self.store, self.imports, "contrast", destination)
        self.assertEqual(manifest["site"], "contrast")
        self.assertIn("Fresh edition", (destination / "index.html").read_text())
        self.assertTrue((destination / "MANIFEST.sha256").is_file())

    def test_refuses_incomplete_and_changed_image(self):
        digest = self.add_image("slot-one")
        self.store.save(record("slot-one", digest, title="Baseline"))
        self.store.start_refresh("contrast", "Fortnight 1")
        with self.assertRaisesRegex(ContentError, "incomplete"):
            build_candidate(self.store, self.imports, "contrast", self.root / "incomplete")
        self.store.save(record("slot-one", digest, title="Fresh edition"))
        self.store.approve("contrast", "slot-one", "jason")
        (self.imports / "contrast" / "slot-one" / f"{digest}.jpg").write_bytes(b"changed")
        with self.assertRaisesRegex(ContentError, "missing or changed"):
            build_candidate(self.store, self.imports, "contrast", self.root / "changed")
        self.assertFalse((self.root / "changed").exists())


if __name__ == "__main__":
    unittest.main()
