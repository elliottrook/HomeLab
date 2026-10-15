"""Synthetic checks for the read-only Aster Books sections."""
from datetime import datetime, timezone
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from books_data import PAGES, page_records
from hub_feeds import book_catalogue


ROOT = Path(__file__).resolve().parents[1]


class BooksTests(unittest.TestCase):
    def sample(self):
        return {'schema_version': 1,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'items': [
                    {'authority': 'audiobookshelf', 'media_type': 'audiobook',
                     'authority_id': 'a1', 'title': 'A [Book]', 'token': 'discard'},
                    {'authority': 'calibre', 'media_type': 'ebook',
                     'authority_id': 'e1', 'title': 'Example Ebook'},
                    {'authority': 'audiobookshelf', 'media_type': 'podcast',
                     'authority_id': 'p1', 'title': 'Example Podcast'},
                    {'authority': 'jellyfin', 'media_type': 'movie',
                     'authority_id': 'm1', 'title': 'Not a book'}]}

    def test_catalogue_is_filtered_bounded_and_searchable(self):
        rows = book_catalogue(self.sample())
        self.assertEqual([row['kind'] for row in rows],
                         ['audiobook', 'ebook', 'podcast'])
        self.assertEqual(rows[0]['title'], 'A (Book)')
        self.assertNotIn('token', rows[0])
        self.assertEqual([row['title'] for row in page_records(rows, 'ebooks', 'EXAMPLE')],
                         ['Example Ebook'])
        self.assertEqual(page_records(rows, 'podcasts', 'absent'), [])

    def test_windows_use_shared_hero_search_and_approved_icons(self):
        shared = ET.parse(ROOT / '1080i/IncludesBooks.xml')
        self.assertIsNotNone(shared.find('.//control[@id="301"]'))
        self.assertIsNotNone(shared.find('.//control[@id="500"]'))
        self.assertIsNotNone(shared.find('.//param[@name="id"][@value="501"]'))
        self.assertIsNotNone(shared.find('.//param[@name="id"][@value="502"]'))
        self.assertIsNotNone(shared.find('.//param[@name="id"][@value="503"]'))
        text = (ROOT / '1080i/IncludesBooks.xml').read_text()
        for icon in ('21-books-app.png', '12-audiobooks.png', '22-podcasts-app.png'):
            self.assertIn(icon, text)
        self.assertIn('ui-hero-bottom-fade.png', text)
        for page, identifier in PAGES.items():
            path = ROOT / f'1080i/custom_{identifier - 10000}_{"books" if page == "home" else page}.xml'
            window = ET.parse(path)
            self.assertEqual(window.getroot().get('id'), str(identifier - 10000))
            self.assertEqual(window.find('.//param[@name="page"]').get('value'), page)


if __name__ == '__main__':
    unittest.main()
