import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import build_voice_search as build


class VoiceBuildTests(unittest.TestCase):
    def test_exact_predecessors_produce_bounded_addon_and_replacements(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); before = root / 'before'; before.mkdir()
            # Build fixtures by replacing the pins for this isolated unit test.
            search = (Path(__file__).parent / 'search_native/default.py').read_bytes()
            window = (Path(__file__).parent / 'search_native/overlay/custom_1127_search.xml').read_bytes()
            keymap = (Path(__file__).parent.parent / 'remote/g20s-pro-plus.xml').read_bytes()
            rows = {'runtime-search.py': search, 'custom_1127_search.xml': window,
                    'g20s-pro-plus.xml': keymap}
            old = build.PINS
            build.PINS = {name: hashlib.sha256(raw).hexdigest() for name, raw in rows.items()}
            try:
                for name, raw in rows.items(): (before / name).write_bytes(raw)
                value = build.build(before, root / 'out')
            finally:
                build.PINS = old
            manifest = json.loads((root / 'out/manifest.json').read_text())
            self.assertEqual(value, hashlib.sha256((root / 'out/manifest.json').read_bytes()).hexdigest())
            self.assertEqual(manifest['kind'], 'hp-voice-search-pilot.v1')
            self.assertGreaterEqual(len(manifest['addon']['files']), 13)
            self.assertEqual(len(manifest['replacements']), 3)
            self.assertEqual(manifest['helper']['path'], 'deploy_voice_search.py')
            xml = ET.parse(root / 'out/payload/g20s-pro-plus.xml')
            self.assertEqual(xml.find("./global/keyboard/key[@id='582']").text,
                             'RunScript(script.astervoice.v2lab)')
            self.assertIn("command=='voice'", (root / 'out/payload/runtime-search.py').read_text())

    def test_refuses_existing_output_and_predecessor_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); before = root / 'before'; before.mkdir()
            for name in build.PINS: (before / name).write_bytes(b'wrong')
            with self.assertRaises(ValueError): build.build(before, root / 'out')
            (root / 'exists').mkdir()
            with self.assertRaises(ValueError): build.build(before, root / 'exists')


if __name__ == '__main__':
    unittest.main()
