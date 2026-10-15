"""Synthetic playlist generation tests; no Kodi runtime or library writes."""
import unittest
import xml.etree.ElementTree as ET
from filter_library import build_playlist, CATEGORIES


class FilterTests(unittest.TestCase):
    def test_all_categories_keep_their_scope(self):
        for filename, (kind, name, tag) in CATEGORIES.items():
            root = ET.fromstring(build_playlist(filename, 'Drama', 8))
            self.assertEqual(root.get('type'), kind)
            self.assertEqual(root.findtext('name'), name)
            self.assertEqual(root.findtext('match'), 'all')
            self.assertEqual(root.findtext("rule[@field='tag']/value"), tag)
            self.assertEqual(root.findtext("rule[@field='genre']/value"), 'Drama')
            threshold = float(root.findtext("rule[@field='rating']/value"))
            self.assertGreater(8, threshold)
            self.assertLess(7.99, threshold)

    def test_genre_is_escaped_not_executable(self):
        genre = 'Sci-Fi & Fantasy <script>'
        root = ET.fromstring(build_playlist('tv-shows.xsp', genre))
        self.assertEqual(root.findtext("rule[@field='genre']/value"), genre)

    def test_empty_filters_keep_only_category(self):
        self.assertEqual(len(ET.fromstring(build_playlist('movies.xsp')).findall('rule')), 1)

    def test_unknown_category_fails_closed(self):
        with self.assertRaises(KeyError):
            build_playlist('../anything.xsp')


if __name__ == '__main__':
    unittest.main()
