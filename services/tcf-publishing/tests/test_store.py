from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content import ContentError, ContentRecord
from store import ContentStore


def record(site="contrast", **changes):
    value = dict(
        id="shared-frame", site=site, asset_path=f"{site}/shared-frame.jpg",
        image_sha256="b" * 64, collection="people", title="Shared Frame",
        alt_text="A person laughing beside a painted doorway",
        story=" ".join(["story"] * 45), full_story="", story_mode="factual",
        orientation="portrait", focal_point="50% 40%", rights_status="verified",
        consent_status="verified", credit="Jason Elliott", sample=False,
    )
    value.update(changes)
    return ContentRecord.from_dict(value)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = ContentStore(Path(self.temporary.name) / "content.db")

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def test_edit_invalidates_approval(self):
        self.assertEqual(self.store.save(record()), 1)
        self.store.approve("contrast", "shared-frame", "jason")
        self.assertIsNotNone(self.store.current_approval("contrast", "shared-frame"))
        self.assertEqual(self.store.save(record(title="Edited")), 2)
        self.assertIsNone(self.store.current_approval("contrast", "shared-frame"))

    def test_cross_publication_creates_independent_unapproved_record(self):
        self.store.save(record())
        self.store.approve("contrast", "shared-frame", "jason")
        self.assertEqual(self.store.copy_to_site("contrast", "shared-frame", "closet"), 1)
        copied, version = self.store.latest("closet", "shared-frame")
        self.assertEqual((copied.site, version), ("closet", 1))
        self.assertIsNone(self.store.current_approval("closet", "shared-frame"))

    def test_sample_cannot_be_approved(self):
        self.store.save(record(sample=True))
        with self.assertRaises(ContentError):
            self.store.approve("contrast", "shared-frame", "jason")

    def test_sample_flag_cannot_be_removed_by_ordinary_save(self):
        self.store.save(record(sample=True))
        with self.assertRaisesRegex(ContentError, "explicit promotion"):
            self.store.save(record(sample=False))

    def test_promotion_requires_phrase_import_and_publication_readiness(self):
        self.store.save(record(sample=True, asset_path="assets/sample.jpg"))
        with self.assertRaisesRegex(ContentError, "confirmation"):
            self.store.promote("contrast", "shared-frame", "PROMOTE")
        with self.assertRaisesRegex(ContentError, "imported photograph"):
            self.store.promote("contrast", "shared-frame", "PROMOTE REAL CONTENT")
        self.store.save(record(sample=True, asset_path="imports/shared-frame/abc.jpg"))
        self.assertEqual(self.store.promote(
            "contrast", "shared-frame", "PROMOTE REAL CONTENT"), 3)
        promoted, version = self.store.latest("contrast", "shared-frame")
        self.assertEqual((promoted.sample, version), (False, 3))
        self.assertIsNone(self.store.current_approval("contrast", "shared-frame"))

    def test_latest_list_is_site_scoped_and_returns_only_current_versions(self):
        self.store.save(record(id="contrast-frame"))
        self.store.save(record(id="contrast-frame", title="Second version"))
        self.store.save(record(site="closet", id="closet-frame"))
        listed = self.store.list_latest("contrast")
        self.assertEqual([(item.id, version) for item, version in listed], [("contrast-frame", 2)])
        self.assertEqual(listed[0][0].title, "Second version")


if __name__ == "__main__":
    unittest.main()
