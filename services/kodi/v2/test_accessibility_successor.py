import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_accessibility_successor import build


class AccessibilitySuccessorTests(unittest.TestCase):
    def test_build_guards_new_animation_only_in_pinned_predecessor(self):
        raw = (b'<includes><include name="AsterPageBackground"><animation effect="fade" '
               b'start="0" end="100" time="180">WindowOpen</animation></include></includes>')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / "Includes.xml"; source.write_bytes(raw)
            output = root / "stage"
            with patch("build_accessibility_successor.PREDECESSOR",
                       __import__("hashlib").sha256(raw).hexdigest()):
                pin = build(source, output)
            self.assertEqual(len(pin), 64)
            changed = (output / "payload/.kodi/addons/skin.asterhome/1080i/Includes.xml").read_text()
            self.assertIn("!Skin.HasSetting(AsterReducedMotion)", changed)

    def test_build_rejects_drift(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root / "Includes.xml"; source.write_text("<includes/>")
            with self.assertRaisesRegex(ValueError, "predecessor"):
                build(source, root / "stage")


if __name__ == "__main__":
    unittest.main()
