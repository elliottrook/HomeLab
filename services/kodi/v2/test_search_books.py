import unittest

from search_books import search_books


class BooksSearchTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {'kind': 'ebook', 'id': '12', 'title': 'A River Book', 'detail': 'Ebook · Calibre'},
            {'kind': 'audiobook', 'id': 'audio_12', 'title': 'River Voices', 'detail': 'Audiobook · Audiobookshelf'},
            {'kind': 'podcast', 'id': 'pod-12', 'title': 'The River Show', 'detail': 'Podcast · Audiobookshelf'},
        ]

    def test_all_three_groups_are_stable_and_id_bound(self):
        calls = []
        def catalogue():
            calls.append(1)
            return [row.copy() for row in self.rows]
        groups = search_books(catalogue, 'river')
        self.assertEqual(len(calls), 2)
        self.assertEqual([g.label for g in groups], ['Ebooks', 'Audiobooks', 'Podcasts'])
        self.assertEqual([g.hits[0].identity for g in groups], ['12', 'audio_12', 'pod-12'])

    def test_changed_feed_never_mixes_results(self):
        rows = [self.rows, self.rows[:1]]
        groups = search_books(lambda: rows.pop(0), 'river')
        self.assertEqual([g.state for g in groups], ['unavailable'] * 3)

    def test_invalid_route_id_is_not_displayed_as_openable(self):
        bad = [{**self.rows[1], 'id': 'a,b'}]
        groups = search_books(lambda: bad, 'river')
        self.assertEqual([g.state for g in groups], ['unavailable'] * 3)

    def test_blank_query_does_not_read_feed(self):
        groups = search_books(lambda: self.fail('feed should not be read'), '')
        self.assertEqual([g.state for g in groups], ['idle'] * 3)


if __name__ == '__main__':
    unittest.main()
