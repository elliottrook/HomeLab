import unittest
from digest_read_model import read_page, source, MAX_PAGE


def card(title='Story', summary='Aster published summary', extra=''):
    return ('<article class="digest-card"><div class="digest-headline">' + title +
            '</div><p class="digest-summary">' + summary + '</p>' + extra + '</article>')


class DigestReadTests(unittest.TestCase):
    def parse(self, value):
        return read_page(value.encode())

    def test_full_summary_is_not_preview_excerpt(self):
        summary = 'Complete sentence. ' * 100
        page = self.parse(card(summary=summary))
        self.assertEqual(page.cards[0].summary, summary.strip())
        self.assertFalse(page.cards[0].truncated)

    def test_only_reporting_links_not_navigation_or_image_credit(self):
        extra = ('<div class="digest-image-credit"><a href="https://example.org/photo">Photo</a></div>'
                 '<div class="digest-outlets"><a href="https://example.org/story">Outlet</a>'
                 '<span class="rating">Rating</span></div>')
        page = self.parse('<a href="https://example.org/nav">Nav</a>' + card(extra=extra))
        self.assertEqual([(s.label, s.host) for s in page.cards[0].sources], [('Outlet', 'example.org')])

    def test_snapshot_selection_and_stale_page(self):
        first = self.parse(card())
        self.assertEqual(first.select(first.identity, first.cards[0].identity), first.cards[0])
        second = self.parse(card(summary='Corrected summary'))
        with self.assertRaisesRegex(ValueError, 'page-changed'):
            second.select(first.identity, first.cards[0].identity)
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            second.select(second.identity, first.cards[0].identity)

    def test_no_audio_binding_or_playback_api(self):
        page = self.parse(card())
        self.assertFalse(hasattr(page, 'audio_edition'))
        self.assertFalse(hasattr(page.cards[0], 'start'))
        self.assertFalse(hasattr(page, 'play'))

    def test_duplicate_titles_are_all_withheld(self):
        page = self.parse(card() + card('STORY') + card('Unique'))
        self.assertEqual([c.title for c in page.cards], ['Unique'])
        self.assertEqual(page.ambiguous_titles, 1)

    def test_missing_summary_is_not_full_article(self):
        self.assertEqual(self.parse(card(summary='')).cards, ())

    def test_nested_inline_content_void_and_ignored_active_markup(self):
        page = self.parse(card(summary='One <strong>two</strong><br>three<script>evil()</script>'))
        self.assertEqual(page.cards[0].summary, 'One two three')

    def test_kodi_and_bidi_commands_stripped(self):
        page = self.parse(card(title='[COLOR red]Title[/COLOR]\u202e', summary='Text\x00\nnext'))
        self.assertEqual(page.cards[0].title, 'Title')
        self.assertEqual(page.cards[0].summary, 'Text next')

    def test_notes_and_field_bounds(self):
        page = self.parse(card(title='x'*300, summary='y'*7000,
            extra='<div class="digest-deviation">Compared <strong>reports</strong></div>'))
        self.assertEqual(len(page.cards[0].title), 240)
        self.assertEqual(len(page.cards[0].summary), 6000)
        self.assertTrue(page.cards[0].truncated)
        self.assertEqual(page.cards[0].differences, 'Compared reports')

    def test_source_requires_narrow_https_display_reference(self):
        for url in ('http://example.org/a', 'https://127.0.0.1/a', 'https://[::1]/a',
                    'https://user@example.org/a', 'https://example.org:44/a',
                    'https://host.local/a', 'https://local/a', 'https://foo.internal/a',
                    'https://example.org./a', 'https://example..org/a', 'https://-foo.org/a',
                    'https://example.org/ bad', 'https://example.org/\\bad',
                    'https://example.org/%0abad', 'plugin://addon/a',
                    'https://2130706433/a', 'https://foo.123/a', 'https://example.org:\n/a'):
            with self.subTest(url=url):
                self.assertIsNone(source('Outlet', url))
        self.assertEqual(source('Outlet', 'https://example.org:443/a?q=b').host, 'example.org')
        self.assertIsNone(source('', 'https://example.org/a'))

    def test_repeated_source_deduplication(self):
        anchor = '<a href="https://example.org/a">Outlet</a>'
        page = self.parse(card(extra='<div class="digest-outlets">' + anchor*3 + '</div>'))
        self.assertEqual(len(page.cards[0].sources), 1)

    def test_source_count_bound(self):
        anchors = ''.join('<a href="https://example.org/%d">Outlet</a>' % n for n in range(9))
        with self.assertRaisesRegex(ValueError, 'too-many-reading-sources'):
            self.parse(card(extra='<div class="digest-outlets">' + anchors + '</div>'))

    def test_reject_incomplete_malformed_nested_or_duplicate_fields(self):
        for value in (card()[:-10], card(summary='<strong>bad'), card(extra=card()),
                      card(extra='<p class="digest-summary">Second</p>')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse(value)

    def test_page_count_depth_and_encoding_bounds(self):
        for raw in (b'x'*(MAX_PAGE+1), b'\xff', (card()*81).encode(),
                    card(extra='<div>'*41 + '</div>'*41).encode(), 'not bytes'):
            with self.subTest(kind=type(raw)), self.assertRaises(ValueError):
                read_page(raw)

    def test_empty_page_is_truthfully_empty(self):
        self.assertEqual(self.parse('<html>No briefing</html>').cards, ())


if __name__ == '__main__':
    unittest.main()
