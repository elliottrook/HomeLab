#!/usr/bin/env python3

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_epub_consumer import build


ACTIVE = Path('/private/tmp/aster-books-active-20261026.py')


class ConsumerBuildTests(unittest.TestCase):
    @unittest.skipUnless(ACTIVE.is_file(), 'active HP Books snapshot unavailable')
    def test_package_is_repeatable_and_preserves_active_hero(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / 'first', root / 'second'
            self.assertEqual(build(ACTIVE, first), build(ACTIVE, second))
            manifest = json.loads((first / 'manifest.json').read_text())
            self.assertEqual(manifest['kind'], 'aster-hp-compiled-epub-consumer-v1')
            self.assertTrue(manifest['hp_only'])
            self.assertEqual(
                manifest['predecessor_books_sha256'], hashlib.sha256(ACTIVE.read_bytes()).hexdigest())
            books = (first / 'books_data.py').read_bytes()
            self.assertEqual(books.count(b'def _hero_rows('), ACTIVE.read_bytes().count(b'def _hero_rows('))
            self.assertIn(b'def compiled_reader_target(', books)
            self.assertEqual(set(manifest['unit_sha256']), {
                'storage-aster\\x2dreader-ready.mount',
                'storage-aster\\x2dreader-ready.automount',
                'storage-aster\\x2dreader-generations.mount',
                'storage-aster\\x2dreader-generations.automount',
            })
            for relative, wanted in manifest['files'].items():
                self.assertEqual(hashlib.sha256((first / relative).read_bytes()).hexdigest(), wanted)


if __name__ == '__main__':
    unittest.main()
