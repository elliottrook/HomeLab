import hashlib
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import media_top_rail
from build_media_top_rail import build


HERE = Path(__file__).resolve().parent
SOURCE = Path("/private/tmp/aster-cross-Home.xml")


class MediaTopRailTests(unittest.TestCase):
    def source(self):
        if SOURCE.is_file() and hashlib.sha256(SOURCE.read_bytes()).hexdigest() == media_top_rail.ACCEPTED_HOME:
            return SOURCE.read_bytes()
        self.skipTest("exact HP Media Home fixture is not present")

    def test_semantics_are_preserved_and_labels_fit_before_clock(self):
        raw = self.source(); result = media_top_rail.transform(raw)
        root = ET.fromstring(result); rail = root.find(".//control[@id='23']")
        self.assertEqual(rail.find("control[@id='137']/onclick").text,
                         "RunScript(script.asteracquisition)")
        youtube = rail.find("control[@id='136']")
        self.assertEqual(int(youtube.findtext("left"))
                         + int(youtube.findtext("width")), 1738)
        self.assertNotEqual(hashlib.sha256(result).hexdigest(),
                            media_top_rail.ACCEPTED_HOME)

    def test_wrong_source_and_second_application_fail_closed(self):
        raw = self.source()
        with self.assertRaisesRegex(ValueError, "predecessor"):
            media_top_rail.transform(raw + b"\n")
        with self.assertRaisesRegex(ValueError, "predecessor"):
            media_top_rail.transform(media_top_rail.transform(raw))

    def test_build_is_immutable_and_pinned(self):
        raw = self.source()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); home = root / "Home.xml"; home.write_bytes(raw)
            output = root / "stage"; pin = build(home, output)
            self.assertEqual(hashlib.sha256((output / "manifest.json").read_bytes()).hexdigest(), pin)
            with self.assertRaisesRegex(ValueError, "build-path"):
                build(home, output)


if __name__ == "__main__":
    unittest.main()
