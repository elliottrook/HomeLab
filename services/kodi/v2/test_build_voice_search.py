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
            search_manifest = build.encoded({'files': [{
                'path': 'default.py', 'bytes': len(search),
                'sha256': hashlib.sha256(search).hexdigest(),
            }]})
            family_manifest = build.encoded({
                'components': {'aster-global-search-ui22': {
                    'files': 1,
                    'manifest_sha256': hashlib.sha256(search_manifest).hexdigest(),
                }},
                'skin': {'1080i/custom_1127_search.xml':
                         hashlib.sha256(window).hexdigest()},
            })
            rows = {'runtime-search.py': search, 'custom_1127_search.xml': window,
                    'g20s-pro-plus.xml': keymap,
                    'search-manifest.json': search_manifest,
                    'family-manifest.json': family_manifest}
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
            self.assertEqual(len(manifest['replacements']), 5)
            self.assertEqual({row['path'] for row in manifest['installs']},
                             {build.HWDB_NAME, *build.PULSE_FILES,
                              build.EVENTLIRCD_NAME})
            for row in manifest['installs']:
                self.assertEqual(row['sha256'], hashlib.sha256(
                    (root / 'out/payload' / row['path']).read_bytes()).hexdigest())
            self.assertEqual(manifest['helper']['path'], 'deploy_voice_search.py')
            xml = ET.parse(root / 'out/payload/g20s-pro-plus.xml')
            self.assertEqual(xml.find('./global/keyboard/browser_search').text,
                             'RunScript(script.astervoice.v2lab)')
            self.assertIn('KEYBOARD_KEY_c00cf=search',
                          (root / 'out/payload' / build.HWDB_NAME).read_text())
            self.assertIn("command=='voice'", (root / 'out/payload/runtime-search.py').read_text())
            search_result = json.loads(
                (root / 'out/payload/search-manifest.json').read_text())
            self.assertEqual(search_result['files'][0]['sha256'], hashlib.sha256(
                (root / 'out/payload/runtime-search.py').read_bytes()).hexdigest())
            family_result = json.loads(
                (root / 'out/payload/family-manifest.json').read_text())
            self.assertEqual(
                family_result['components']['aster-global-search-ui22']['manifest_sha256'],
                hashlib.sha256((root / 'out/payload/search-manifest.json').read_bytes()).hexdigest())

    def test_refuses_existing_output_and_predecessor_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); before = root / 'before'; before.mkdir()
            for name in build.PINS: (before / name).write_bytes(b'wrong')
            with self.assertRaises(ValueError): build.build(before, root / 'out')
            (root / 'exists').mkdir()
            with self.assertRaises(ValueError): build.build(before, root / 'exists')


if __name__ == '__main__':
    unittest.main()
