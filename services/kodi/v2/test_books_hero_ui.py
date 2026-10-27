import ast
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from books_hero_ui import append_visibility, extend_books_data, extend_home, extend_includes


class BooksHeroUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = Path('/private/tmp/aster-books-active')

    def test_active_hp_snapshot_transforms_and_parses(self):
        if not self.snapshot.exists():self.skipTest('live snapshot unavailable')
        data = extend_books_data((self.snapshot/'books_data.py').read_bytes())
        ast.parse(data)
        includes = ET.fromstring(extend_includes((self.snapshot/'IncludesBooks.xml').read_bytes()))
        home = ET.fromstring(extend_home((self.snapshot/'custom_1110_books.xml').read_bytes()))
        self.assertEqual(home.findtext('defaultcontrol'), '110')
        self.assertIsNotNone(includes.find(".//control[@id='307']"))
        text = data.decode()
        self.assertIn("recommendations(items, recent)", text)
        self.assertNotIn("Control.SetFocus({first_row}", text)

    def test_transform_refuses_reapplication(self):
        if not self.snapshot.exists():self.skipTest('live snapshot unavailable')
        first = extend_books_data((self.snapshot/'books_data.py').read_bytes())
        with self.assertRaises(ValueError):extend_books_data(first)

    def test_mixed_visibility_is_split_into_native_and_nodes(self):
        control = ET.Element('control')
        ET.SubElement(control, 'visible').text = '!A | !B'
        append_visibility(control, 'C | D')
        self.assertEqual([node.text for node in control.findall('visible')],
                         ['!A | !B', 'C | D'])


if __name__ == '__main__':unittest.main()
