from pathlib import Path
import hashlib
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET

from build_compiled_epub_reader import build, layout


class CompiledEpubReaderTests(unittest.TestCase):
    def test_normal_reader_is_repeatable_pinned_and_offline(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / 'first', root / 'second'
            self.assertEqual(build(first), build(second))
            manifest = json.loads((first / 'bundle.json').read_text())
            self.assertEqual(manifest['kind'], 'aster-books-compiler-reader-v1')
            self.assertEqual(manifest['compiler_commit'], 'fc91fcd4')
            self.assertTrue(manifest['hp_only'])
            self.assertTrue(manifest['active'])
            self.assertTrue(manifest['normal_entry'])
            self.assertFalse(manifest['network'])
            self.assertFalse(manifest['shared_progress'])
            self.assertNotIn('selection.json', manifest['files'])
            for relative, wanted in manifest['files'].items():
                self.assertEqual(
                    hashlib.sha256((first / relative).read_bytes()).hexdigest(), wanted)

    def test_entry_accepts_only_pinned_numeric_books_from_books_windows(self):
        source = (Path(__file__).parent / 'compiled_epub_reader/default.py').read_text()
        self.assertIn('len(sys.argv) == 3', source)
        self.assertIn('verify(sys.argv[1], sys.argv[2])', source)
        self.assertIn('previous_window in (10000, 11110, 11118)', source)
        self.assertNotIn('selection.json', source)
        self.assertNotIn('http://', source)
        self.assertNotIn('https://', source)

    def test_layout_keeps_reading_page_and_centered_floating_controls(self):
        root = ET.fromstring(layout())
        self.assertEqual(root.findtext('backgroundcolor'), 'ffe6dac8')
        self.assertEqual(root.findtext('defaultcontrol'), '500')
        self.assertEqual(root.find('.//control[@id="500"]/ondown').text, '201')
        for identity in range(201, 208):
            control = root.find('.//control[@id="' + str(identity) + '"]')
            self.assertEqual(control.findtext('onup'), '500')
        self.assertIn('gold marks the current sentence', ET.tostring(root).decode())


if __name__ == '__main__':
    unittest.main()
