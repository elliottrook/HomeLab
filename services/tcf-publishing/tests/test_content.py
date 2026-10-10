import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content import Approval, ContentError, ContentRecord, validate_site_batch, word_count


def record(**changes):
    value = dict(
        id="after-the-weather",
        site="contrast",
        asset_path="landscapes/alpine-dawn.png",
        image_sha256="a" * 64,
        collection="landscapes",
        title="After the Weather",
        alt_text="Dawn opening over a mist-filled mountain lake",
        story=" ".join(["quiet"] * 45),
        full_story="",
        story_mode="fictional",
        orientation="landscape",
        focal_point="50% 50%",
        rights_status="verified",
        consent_status="not-applicable",
        credit="Sample source",
        sample=False,
    )
    value.update(changes)
    return ContentRecord.from_dict(value)


class ContentTests(unittest.TestCase):
    def test_word_count_handles_apostrophes_and_hyphens(self):
        self.assertEqual(word_count("Jason's softly-lit frame"), 3)

    def test_target_record_has_no_warning(self):
        self.assertEqual(record().warnings(), [])

    def test_soft_warning_does_not_block(self):
        item = record(story=" ".join(["word"] * 81))
        self.assertEqual(len(item.warnings()), 1)

    def test_hard_limits_block(self):
        with self.assertRaises(ContentError):
            record(story=" ".join(["word"] * 101))
        with self.assertRaises(ContentError):
            record(full_story=" ".join(["word"] * 161))

    def test_traversal_blocks_and_unknown_rights_prevent_approval(self):
        with self.assertRaises(ContentError):
            record(asset_path="../private/original.raw")
        self.assertIn("rights are not verified", record(rights_status="unknown").approval_blockers())

    def test_any_public_edit_invalidates_approval(self):
        original = record()
        approval = Approval(original.id, 1, original.public_hash(), "jason", "2026-10-09T12:00:00Z")
        self.assertTrue(approval.matches(original))
        self.assertFalse(approval.matches(record(alt_text="A changed description")))
        self.assertFalse(approval.matches(record(story=" ".join(["changed"] * 45))))

    def test_sample_flag_changes_approved_public_payload(self):
        self.assertNotEqual(record(sample=True).public_hash(), record(sample=False).public_hash())

    def test_site_change_invalidates_approval_and_unknown_site_is_rejected(self):
        original = record(site="contrast")
        approval = Approval(original.id, 1, original.public_hash(), "jason", "2026-10-09T12:00:00Z")
        self.assertFalse(approval.matches(record(site="closet")))
        with self.assertRaises(ContentError):
            record(site="other")

    def test_release_batch_rejects_cross_site_records(self):
        validate_site_batch([record(id="contrast-one")], "contrast")
        with self.assertRaises(ContentError):
            validate_site_batch(
                [record(id="contrast-one"), record(id="closet-one", site="closet")],
                "contrast",
            )

    def test_sample_content_can_be_previewed_but_never_approved(self):
        item = record(sample=True, rights_status="unknown", consent_status="unknown")
        self.assertEqual(len(item.approval_blockers()), 3)
        approval = Approval(item.id, 1, item.public_hash(), "jason", "2026-10-09T12:00:00Z")
        self.assertFalse(approval.matches(item))

    def test_annotation_is_plain_bounded_and_part_of_approved_payload(self):
        original = record(annotation_text="After the Weather", annotation_x=80, annotation_y=38)
        self.assertNotEqual(original.public_hash(), record(annotation_text="A different title").public_hash())
        with self.assertRaisesRegex(ContentError, "plain text"):
            record(annotation_text="<strong>Not plain</strong>")
        with self.assertRaisesRegex(ContentError, "between 5 and 95"):
            record(annotation_x=99)


if __name__ == "__main__":
    unittest.main()
