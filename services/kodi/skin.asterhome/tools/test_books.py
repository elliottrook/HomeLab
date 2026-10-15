"""Synthetic checks for the read-only Aster Books sections."""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import json
import base64
import tempfile
import unittest
import xml.etree.ElementTree as ET

from books_data import PAGES, cached_cover, cover_filename, page_records
from hub_feeds import book_catalogue
from pilot_books_feed import calibre_items
from pilot_books_covers import QUERY, validated_covers


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

    def test_full_calibre_library_is_not_cut_off_at_200(self):
        sample = self.sample()
        sample['items'] = [
            {'authority': 'calibre', 'media_type': 'ebook',
             'authority_id': str(index), 'title': f'Book {index}'}
            for index in range(1, 506)]
        self.assertEqual(len(page_records(book_catalogue(sample), 'ebooks')), 505)

    def test_calibre_projection_bounds_titles_and_fields(self):
        source = json.dumps([{'id': 1, 'title': 'A' * 196, 'path': '/private'},
                             {'id': 2, 'title': 'Example'}]).encode()
        with patch('pilot_books_feed.remote', return_value=source):
            items = calibre_items()
        self.assertEqual(len(items), 2)
        self.assertEqual(len(items[0]['title']), 160)
        self.assertTrue(items[0]['title'].endswith('…'))
        self.assertNotIn('path', items[0])

    def test_cover_cache_uses_opaque_key_and_rejects_symlink(self):
        row = {'kind': 'audiobook', 'id': 'li_example', 'title': 'Private title'}
        self.assertNotIn('Private title', cover_filename(row))
        with tempfile.TemporaryDirectory() as directory:
            cover = Path(directory) / cover_filename(row)
            self.assertIsNone(cached_cover(directory, row))
            cover.write_bytes(b'\xff\xd8\xff' + b'cover')
            self.assertEqual(cached_cover(directory, row), str(cover))
            cover.unlink()
            cover.symlink_to(Path(directory) / 'elsewhere.jpg')
            self.assertIsNone(cached_cover(directory, row))

    def test_cover_transfer_requires_known_item_and_jpeg(self):
        rows = [{'kind': 'audiobook', 'id': 'li_example', 'title': 'Example'}]
        jpeg = base64.b64encode(b'\xff\xd8\xff' + b'image').decode()
        raw = json.dumps([{'id': 'li_example', 'jpeg': jpeg}]).encode()
        self.assertEqual(validated_covers(raw, rows), {'li_example': b'\xff\xd8\xffimage'})
        with self.assertRaises(ValueError):
            validated_covers(raw.replace(b'li_example', b'unknown'), rows)
        with self.assertRaises(ValueError):
            validated_covers(json.dumps([{'id': 'li_example', 'jpeg': 'ZGF0YQ=='}]).encode(), rows)
        self.assertIn('sqlite.OPEN_READONLY', QUERY)

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
