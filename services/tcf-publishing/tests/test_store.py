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

    def test_fortnightly_refresh_requires_every_slot_changed_and_approved(self):
        self.store.save(record(id="slot-one"))
        self.store.save(record(id="slot-two"))
        status = self.store.start_refresh("contrast", "24 October edition")
        self.assertEqual((status["total"], status["replaced"], status["ready"]), (2, 0, False))
        self.store.save(record(id="slot-one", title="Replacement one"))
        self.store.approve("contrast", "slot-one", "jason")
        status = self.store.edition_status("contrast")
        self.assertEqual((status["replaced"], status["approved"], status["ready"]), (1, 1, False))
        self.store.save(record(id="slot-two", title="Replacement two"))
        self.store.approve("contrast", "slot-two", "jason")
        status = self.store.edition_status("contrast")
        self.assertEqual((status["replaced"], status["approved"], status["ready"]), (2, 2, True))

    def test_only_one_active_refresh_per_site(self):
        self.store.save(record())
        self.store.start_refresh("contrast", "First")
        with self.assertRaisesRegex(ContentError, "already in progress"):
            self.store.start_refresh("contrast", "Second")

    def test_slot_removal_is_explicit_reversible_and_non_destructive(self):
        self.store.save(record(id="kept-slot"))
        self.store.save(record(id="retired-slot"))
        self.store.start_refresh("contrast", "Smaller edition")
        with self.assertRaisesRegex(ContentError, "confirmation"):
            self.store.set_slot_removal("contrast", "retired-slot", True, "REMOVE")
        status = self.store.set_slot_removal(
            "contrast", "retired-slot", True, "REMOVE SLOT")
        self.assertEqual(status["removed"], ["retired-slot"])
        self.assertEqual(self.store.latest("contrast", "retired-slot")[0].id, "retired-slot")
        status = self.store.set_slot_removal("contrast", "retired-slot", False)
        self.assertEqual(status["removed"], [])
        self.assertFalse(status["ready"])

    def test_edition_manifest_lists_pending_approved_and_removed_slots(self):
        self.store.save(record(id="pending-slot"))
        self.store.save(record(id="approved-slot"))
        self.store.save(record(id="removed-slot"))
        self.store.start_refresh("contrast", "Manifest candidate")
        self.store.save(record(id="approved-slot", title="New approved work"))
        self.store.approve("contrast", "approved-slot", "jason")
        self.store.set_slot_removal("contrast", "removed-slot", True, "REMOVE SLOT")
        manifest = self.store.edition_manifest("contrast")
        self.assertEqual(
            {slot["id"]: slot["state"] for slot in manifest["slots"]},
            {"approved-slot": "approved", "pending-slot": "awaiting replacement",
             "removed-slot": "complete"},
        )
        self.assertFalse(manifest["ready"])


if __name__ == "__main__":
    unittest.main()
