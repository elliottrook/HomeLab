from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_youtube_focus_successor import build
from youtube_focus_successor import COMMAND, transform


SOURCE = Path("/private/tmp/aster-owner-review-candidate2/payload/.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml")


class YouTubeFocusSuccessorTests(unittest.TestCase):
    def setUp(self):
        if not SOURCE.is_file(): self.skipTest("exact-focus-fixture-unavailable")

    def test_delays_focus_without_changing_rows(self):
        root = ET.fromstring(transform(SOURCE.read_bytes()))
        self.assertEqual(root.findtext("onload"), COMMAND)
        for identity in (9530, 9531, 9532):
            self.assertIsNotNone(root.find(f".//control[@id='{identity}']"))

    def test_build_is_immutable(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            output = Path(temporary) / "candidate"
            pin = build(SOURCE, output)
            self.assertEqual(len(pin), 64)
            with self.assertRaisesRegex(ValueError, "output"):
                build(SOURCE, output)


if __name__ == "__main__": unittest.main()
