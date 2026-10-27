"""Synthetic checks for the read-only Aster Books sections."""
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import json
import base64
import tempfile
import unittest
import xml.etree.ElementTree as ET

from books_data import PAGES, activate_row, cached_cover, cover_filename, handoff_target, page_records, selected_row
from hub_feeds import book_catalogue, item_timestamp, plain_synopsis
from pilot_books_feed import (audiobook_metadata, calibre_items,
                              epoch_milliseconds, feed_payload, podcast_items)
from pilot_books_covers import QUERY, validated_covers
from pilot_podcast_covers import QUERY as PODCAST_COVER_QUERY, validated_covers as validated_podcast_covers
from pilot_ebook_covers import SOURCE as CALIBRE_COVER_SOURCE, validated_covers as validated_ebook_covers


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

    def test_catalogue_accepts_only_paired_bounded_recommendation_signals(self):
        sample = self.sample()
        sample['items'][0].update(recommendation_score=72,
                                  recommendation_reason='Because you listen to Mystery')
        row = book_catalogue(sample)[0]
        self.assertEqual(row['recommendation_score'], 72.0)
        sample['items'][0].pop('recommendation_reason')
        with self.assertRaises(ValueError):
            book_catalogue(sample)

    def test_full_calibre_library_is_not_cut_off_at_200(self):
        sample = self.sample()
        sample['items'] = [
            {'authority': 'calibre', 'media_type': 'ebook',
             'authority_id': str(index), 'title': f'Book {index}'}
            for index in range(1, 506)]
        self.assertEqual(len(page_records(book_catalogue(sample), 'ebooks')), 505)

    def test_books_sections_sort_real_dates_before_undated_titles(self):
        sample = self.sample()
        sample['items'] = [
            {'authority': 'calibre', 'media_type': 'ebook',
             'authority_id': '1', 'title': 'Undated'},
            {'authority': 'calibre', 'media_type': 'ebook',
             'authority_id': '2', 'title': 'Older',
             'added_at': '2025-01-01T00:00:00Z'},
            {'authority': 'calibre', 'media_type': 'ebook',
             'authority_id': '3', 'title': 'Newest',
             'added_at': '2026-01-01T00:00:00Z'},
        ]
        self.assertEqual([row['title'] for row in
                          page_records(book_catalogue(sample), 'ebooks')],
                         ['Newest', 'Older', 'Undated'])

    def test_calibre_projection_bounds_titles_and_fields(self):
        source = json.dumps([{'id': 1, 'title': 'A' * 196, 'path': '/private',
                              'added_at': '2026-01-01T00:00:00Z'},
                             {'id': 2, 'title': 'Example', 'added_at': None}]).encode()
        with patch('pilot_books_feed.remote', return_value=source):
            items = calibre_items()
        self.assertEqual(len(items), 2)
        self.assertEqual(len(items[0]['title']), 160)
        self.assertTrue(items[0]['title'].endswith('…'))
        self.assertNotIn('path', items[0])
        self.assertEqual(items[0]['added_at'], '2026-01-01T00:00:00Z')

    def test_podcast_projection_excludes_feed_urls_and_unsubscribed_results(self):
        source = json.dumps([{'id': 'pod_1', 'title': 'Example Show',
                              'feedURL': 'https://private.example/rss',
                              'createdAt': None}]).encode()
        with patch('pilot_books_feed.remote', return_value=source):
            items = podcast_items()
        self.assertEqual(items, [{'authority': 'audiobookshelf',
                                  'media_type': 'podcast', 'authority_id': 'pod_1',
                                  'title': 'Example Show', 'description': '',
                                  'added_at': None}])
        self.assertNotIn('feedURL', items[0])

    def test_audiobook_projection_keeps_only_description_and_added_time(self):
        source = json.dumps([{'id': 'book_1', 'description': '<p>Synopsis</p>',
                              'createdAt': '2026-01-01 00:00:00.000 +00:00',
                              'path': '/private/audio'}]).encode()
        with patch('pilot_books_feed.remote', return_value=source):
            items = audiobook_metadata()
        self.assertEqual(items, {'book_1': {
            'description': 'Synopsis',
            'added_at': '2026-01-01 00:00:00.000 +00:00'}})
        self.assertNotIn('path', items['book_1'])

    def test_feed_freshness_records_capture_time_not_source_mtime(self):
        captured = datetime(2026, 10, 17, 16, 0, tzinfo=timezone.utc)
        feed = feed_payload([], 1_600_000_000, captured)
        self.assertEqual(feed['generated_at'], captured.isoformat())
        self.assertEqual(feed['source_updated_at'],
                         datetime.fromtimestamp(1_600_000_000, timezone.utc).isoformat())
        self.assertNotEqual(feed['generated_at'], feed['source_updated_at'])
        with self.assertRaises(ValueError):
            feed_payload([], 1_600_000_000, captured.replace(tzinfo=None))

    def test_item_dates_are_source_owned_timezone_aware_values(self):
        value = self.sample()
        value['items'][0]['added_at'] = '2026-01-02T03:04:05-08:00'
        self.assertEqual(book_catalogue(value)[0]['added_at'],
                         '2026-01-02T11:04:05+00:00')
        self.assertEqual(item_timestamp('2026-01-01 00:00:00.000 +00:00'),
                         '2026-01-01T00:00:00+00:00')
        self.assertIsNone(item_timestamp(None))
        with self.assertRaisesRegex(ValueError, 'time zone'):
            item_timestamp('2026-01-02T03:04:05')
        epoch = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        self.assertEqual(epoch_milliseconds(epoch.timestamp() * 1000),
                         epoch.isoformat())

    def test_synopsis_is_plain_bounded_and_not_markup(self):
        sample = self.sample()
        sample['items'][0]['description'] = ('<p>A &amp; B</p><script>ignore()</script>'
                                              '<p>Second [COLOR red]part</p>')
        row = book_catalogue(sample)[0]
        self.assertEqual(row['synopsis'], 'A & B Second (COLOR red)part')
        self.assertEqual(plain_synopsis('x' * 1200), 'x' * 997 + '…')
        self.assertEqual(plain_synopsis(None), '')

    def test_selected_row_resolves_only_feed_identity(self):
        class Item:
            def getProperty(self, key):
                return {'AsterBooks.Kind': 'podcast', 'AsterBooks.Id': 'p1'}[key]

        class Control:
            def getSelectedItem(self):
                return Item()

        class Window:
            def getFocusId(self):
                return 500

            def getControl(self, control_id):
                return Control()

        records = book_catalogue(self.sample())
        self.assertEqual(selected_row(Window(), 'podcasts', records)['title'], 'Example Podcast')

    def test_selected_row_uses_panel_info_label_when_wrapper_lacks_selection(self):
        class Window:
            def getFocusId(self):
                return 300

            def getControl(self, control_id):
                raise RuntimeError('panel selection unavailable')

        def label(name):
            return {'Container(502).ListItem.Property(AsterBooks.Kind)': 'audiobook',
                    'Container(502).ListItem.Property(AsterBooks.Id)': 'a1'}.get(name, '')

        records = book_catalogue(self.sample())
        self.assertEqual(selected_row(Window(), 'home', records, label)['id'], 'a1')

    def test_handoff_destinations_allow_only_known_id_shapes(self):
        self.assertEqual(handoff_target({'kind': 'ebook', 'id': '505'}),
                         'https://books.elliottrook.com/book/505')
        self.assertEqual(handoff_target({'kind': 'audiobook', 'id': 'li_book-1'}),
                         'plugin://plugin.audio.asterbooks/?action=book&item_id=li_book-1')
        self.assertEqual(handoff_target({'kind': 'podcast', 'id': 'li_show_1'}),
                         'plugin://plugin.audio.asterbooks/?action=episodes&item_id=li_show_1')
        for row in ({'kind': 'ebook', 'id': '../../1'},
                    {'kind': 'podcast', 'id': 'li_1),RunScript(bad)'},
                    {'kind': 'audiobook', 'id': 'li/1'}):
            self.assertIsNone(handoff_target(row))

    def test_audio_handoff_uses_addon_without_feed_token(self):
        class Xbmc:
            commands = []

            def getCondVisibility(self, condition):
                return True

            def executebuiltin(self, command):
                self.commands.append(command)

        class Gui:
            pass

        xbmc = Xbmc()
        activate_row({'kind': 'audiobook', 'id': 'li_book'}, xbmc, Gui())
        activate_row({'kind': 'podcast', 'id': 'li_show'}, xbmc, Gui())
        self.assertEqual(xbmc.commands,
                         ['ActivateWindow(Music,plugin://plugin.audio.asterbooks/?action=book&item_id=li_book,return)',
                          'ActivateWindow(Music,plugin://plugin.audio.asterbooks/?action=episodes&item_id=li_show,return)'])

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

    def test_calibre_cover_transfer_uses_only_known_ids(self):
        rows = [{'kind': 'ebook', 'id': '42', 'title': 'Example'}]
        jpeg = base64.b64encode(b'\xff\xd8\xff' + b'cover').decode()
        payload = json.dumps({'id': '42', 'jpeg': jpeg}).encode() + b'\n'
        self.assertEqual(validated_ebook_covers(payload, rows), {'42': b'\xff\xd8\xffcover'})
        with self.assertRaises(ValueError):
            validated_ebook_covers(payload.replace(b'"42"', b'"43"'), rows)
        self.assertIn('mode=ro&immutable=1', CALIBRE_COVER_SOURCE)

    def test_podcast_covers_require_subscribed_id_and_jpeg(self):
        rows = [{'kind': 'podcast', 'id': 'pod_1', 'title': 'Example'}]
        jpeg = base64.b64encode(b'\xff\xd8\xff' + b'cover').decode()
        payload = json.dumps([{'id': 'pod_1', 'jpeg': jpeg}]).encode()
        self.assertEqual(validated_podcast_covers(payload, rows),
                         {'pod_1': b'\xff\xd8\xffcover'})
        with self.assertRaises(ValueError):
            validated_podcast_covers(payload.replace(b'pod_1', b'unknown'), rows)
        with self.assertRaises(ValueError):
            validated_podcast_covers(payload, [{'kind': 'audiobook', 'id': 'pod_1'}])
        self.assertIn('sqlite.OPEN_READONLY', PODCAST_COVER_QUERY)
        self.assertIn("resolved.startsWith('/podcasts/')", PODCAST_COVER_QUERY)

    def test_windows_use_shared_hero_search_and_approved_icons(self):
        shared = ET.parse(ROOT / '1080i/IncludesBooks.xml')
        self.assertIsNotNone(shared.find('.//control[@id="301"]'))
        self.assertIsNotNone(shared.find('.//control[@id="500"]'))
        self.assertEqual(shared.find('.//control[@id="111"]/ondown').text, '300')
        self.assertEqual(shared.find('.//control[@id="300"]/ondown').text,
                         '$PARAM[firsttile]')
        self.assertEqual(ET.parse(ROOT / '1080i/custom_1110_books.xml').find(
            './/param[@name="firsttile"]').get('value'), '501')
        self.assertIsNotNone(shared.find('.//param[@name="id"][@value="501"]'))
        self.assertIsNotNone(shared.find('.//param[@name="id"][@value="502"]'))
        self.assertIsNotNone(shared.find('.//param[@name="id"][@value="503"]'))
        text = (ROOT / '1080i/IncludesBooks.xml').read_text()
        for icon in ('21-books-app.png', '12-audiobooks.png', '22-podcasts-app.png'):
            self.assertIn(icon, text)
        self.assertIn('ui-hero-bottom-fade.png', text)
        self.assertIn('No subscribed shows yet. Discover podcasts in Audiobookshelf.', text)
        self.assertIn('No subscribed podcasts · discover in Audiobookshelf', text)
        podcast_window = ET.parse(ROOT / '1080i/custom_1120_podcasts.xml')
        self.assertEqual(podcast_window.find('.//param[@name="emptylabel"]').get('value'),
                         'No subscribed shows yet · add one in Audiobookshelf')
        self.assertIn('Filter my shows', (ROOT / 'tools/books_data.py').read_text())
        for page, identifier in PAGES.items():
            path = ROOT / f'1080i/custom_{identifier - 10000}_{"books" if page == "home" else page}.xml'
            window = ET.parse(path)
            self.assertEqual(window.getroot().get('id'), str(identifier - 10000))
            self.assertEqual(window.find('.//param[@name="page"]').get('value'), page)

    def test_book_art_cards_follow_cover_shape(self):
        shared = ET.parse(ROOT / '1080i/IncludesBooks.xml')
        for name, portrait, square in (('AsterBooksTile', (190, 260), (260, 260)),
                                       ('AsterBooksSmallTile', (79, 108), (108, 108))):
            tile = shared.find(f'.//include[@name="{name}"]')
            panels = [control for control in tile.findall('control')
                      if control.findtext('colordiffuse') == 'asterIvory']
            self.assertEqual(len(panels), 2)
            self.assertEqual((int(panels[0].findtext('width')),
                              int(panels[0].findtext('height'))), portrait)
            self.assertIn('AsterBooks.Kind),ebook', panels[0].findtext('visible'))
            self.assertEqual((int(panels[1].findtext('width')),
                              int(panels[1].findtext('height'))), square)
            self.assertIn('!String.IsEqual(ListItem.Property(AsterBooks.Kind),ebook)',
                          panels[1].findtext('visible'))
            covers = [control for control in tile.findall('control')
                      if control.find('texture') is not None and
                      control.find('texture').get('diffuse')]
            self.assertEqual(len(covers), 2)
            for cover, dimensions, mask in zip(covers, (portrait, square),
                                                ('ui-poster-mask.png', 'ui-album-mask.png')):
                self.assertEqual((int(cover.findtext('width')),
                                  int(cover.findtext('height'))), dimensions)
                self.assertTrue(cover.find('texture').get('diffuse').endswith(mask))
                self.assertEqual(cover.find('aspectratio').text, 'scale')
            self.assertTrue(all('!String.IsEqual(ListItem.Property(AsterBooks.HasCover),true)'
                                in panel.findtext('visible') for panel in panels))
        for layout in shared.findall('.//focusedlayout'):
            self.assertEqual(layout[-1].tag, 'include')

    def test_script_populated_rows_receive_an_initial_focus(self):
        source = (ROOT / 'tools/books_data.py').read_text()
        self.assertIn('Control.SetFocus({first_row},0,absolute)', source)
        self.assertIn('Control.SetFocus(500,0,absolute)', source)


if __name__ == '__main__':
    unittest.main()
