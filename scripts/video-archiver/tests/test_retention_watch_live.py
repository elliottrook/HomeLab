"""All-user Jellyfin watch adapter fails closed on missing or malformed state."""

from urllib.parse import parse_qs, urlparse
from unittest import TestCase

from video_archiver.retention_reconcile import watch_for_item
from video_archiver.retention_watch_live import collect_user_views


USERS = frozenset({'a', 'b'})


def fetch(url, _headers):
    user = url.split('/Users/')[1].split('/')[0]
    requested = parse_qs(urlparse(url).query)['Ids'][0].split(',')
    items = []
    for item_id in requested:
        if user == 'b' and item_id == 'hidden':
            continue
        items.append({'Id': item_id, 'UserData': {
            'Played': user == 'a' and item_id == 'movie',
            'PlayCount': 1 if user == 'a' and item_id == 'movie' else 0,
            'PlaybackPositionTicks': 0, 'IsFavorite': False,
        }})
    return 200, {'Items': items}


class WatchLiveTests(TestCase):
    def test_complete_user_state_and_hidden_item_hold(self):
        views = collect_user_views(('movie', 'hidden'), user_ids=USERS,
                                   jellyfin_url='http://jellyfin.invalid',
                                   jellyfin_api_key='fixture', fetch=fetch)
        movie = watch_for_item('movie', views, USERS)
        self.assertIsNotNone(movie)
        self.assertTrue(any(row.protected for row in movie))
        self.assertIsNone(watch_for_item('hidden', views, USERS))

    def test_malformed_user_state_aborts_scan(self):
        def incomplete(_url, _headers):
            return 200, {'Items': [{'Id': 'movie', 'UserData': {'Played': False}}]}
        with self.assertRaisesRegex(RuntimeError, 'incomplete'):
            collect_user_views(('movie',), user_ids=USERS,
                               jellyfin_url='http://jellyfin.invalid',
                               jellyfin_api_key='fixture', fetch=incomplete)

    def test_api_error_aborts_scan(self):
        with self.assertRaisesRegex(RuntimeError, 'page failed'):
            collect_user_views(('movie',), user_ids=USERS,
                               jellyfin_url='http://jellyfin.invalid',
                               jellyfin_api_key='fixture', fetch=lambda *_: (503, {}))
