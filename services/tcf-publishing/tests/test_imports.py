from base64 import b64encode
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from content import ContentError
from imports import ImportManager, decode_payload, image_extension, markdown_story


class ImportTests(unittest.TestCase):
    def test_markdown_front_matter_and_markup_are_not_public_story_text(self):
        raw = b"---\ntitle: Private note\n---\n# A title\n" + b"quiet " * 44
        story = markdown_story(raw)
        self.assertNotIn("Private note", story)
        self.assertEqual(story.split()[0:2], ["A", "title"])

    def test_markdown_hard_limit_and_invalid_encoding_fail_closed(self):
        with self.assertRaisesRegex(ContentError, "101 words"):
            markdown_story(("word " * 101).encode())
        with self.assertRaisesRegex(ContentError, "UTF-8"):
            markdown_story(b"\xff\xfe")

    def test_base64_and_image_type_are_bounded(self):
        self.assertEqual(decode_payload(b64encode(b"hello").decode(), 5), b"hello")
        with self.assertRaises(ContentError):
            decode_payload("not base64", 20)
        self.assertEqual(image_extension(b"RIFFxxxxWEBPpayload"), ".webp")
        with self.assertRaises(ContentError):
            image_extension(b"GIF89a")

    def test_site_scope_blocks_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = ImportManager(Path(temporary))
            with self.assertRaisesRegex(ContentError, "scope"):
                manager.import_markdown("contrast", "../escape", b"safe story")

    def test_image_lookup_requires_content_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = ImportManager(Path(temporary))
            digest = "a" * 64
            self.assertEqual(manager.image_path("contrast", "three-small-clouds", digest).name,
                             digest + ".jpg")
            with self.assertRaisesRegex(ContentError, "digest"):
                manager.image_path("contrast", "three-small-clouds", "latest")

    def test_markdown_original_is_site_scoped_and_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = ImportManager(Path(temporary))
            result = manager.import_markdown("closet", "three-small-clouds", b"one two three")
            path = Path(temporary) / "closet" / "three-small-clouds" / "story.md"
            self.assertEqual(result["word_count"], 3)
            self.assertEqual(path.read_bytes(), b"one two three")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
