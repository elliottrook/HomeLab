import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_accessibility_final as final


class AccessibilityFinalTests(unittest.TestCase):
    def test_build_requires_exact_guarded_family(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); files = {}
            for relative in final.FILES:
                path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
                if path.name == "SkinSettings.xml":
                    raw = b'<window><control id="200"/><control id="201"/></window>'
                elif path.suffix == ".xml" and "colors" not in path.parts:
                    raw = (b'<window><animation condition="!Skin.HasSetting(AsterReducedMotion)">'
                           b'WindowOpen</animation></window>')
                else: raw = b'<colors/>'
                path.write_bytes(raw); files[relative] = final.sha(path)
            with patch.object(final, "FILES", files):
                pin = final.build(root, root / "stage")
            self.assertEqual(len(pin), 64)

    def test_rejects_hash_drift(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "file"):
                final.build(Path(folder), Path(folder) / "stage")


if __name__ == "__main__": unittest.main()
