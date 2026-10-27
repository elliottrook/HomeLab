#!/usr/bin/env python3

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from compiled_books_handoff import MARKER, compose


ACTIVE = Path('/private/tmp/aster-books-active-20261026.py')


class HandoffTests(unittest.TestCase):
    def source(self):
        if ACTIVE.is_file():
            return ACTIVE.read_bytes()
        return b"""import sys\nimport hashlib\nimport re\nimport stat\nimport webbrowser\nfrom pathlib import Path\nREADER_BASE = 'https://books.elliottrook.com'\ndef handoff_target(row): return 'x'\ndef activate_row(row, xbmc, xbmcgui):\n    destination = handoff_target(row)\n    if destination is None:\n        pass\n    elif row['kind'] == 'ebook':\n        if sys.platform == 'darwin' and webbrowser.open(destination):\n            pass\n        else:\n            pass\n"""

    def test_preserves_active_source_and_adds_only_bounded_handoff(self):
        source = self.source()
        result = compose(source)
        self.assertIn(MARKER.encode(), result)
        self.assertIn(b'def compiled_reader_target(', result)
        self.assertIn(b'compiled = compiled_target(row)', result)
        self.assertEqual(result.count(b'def _hero_rows('), source.count(b'def _hero_rows('))
        self.assertEqual(result.count(b'def books_hero_action('), source.count(b'def books_hero_action('))
        compile(result, 'books_data.py', 'exec')

    def test_refuses_recomposition(self):
        with self.assertRaisesRegex(ValueError, 'already-present'):
            compose(compose(self.source()))


if __name__ == '__main__':
    unittest.main()
