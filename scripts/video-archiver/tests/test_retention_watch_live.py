"""All-user Jellyfin watch adapter fails closed on missing or malformed state."""

import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from unittest import TestCase

from video_archiver.retention_policy import UserWatch
from video_archiver.retention_reconcile import CompleteUserView, watch_for_item
from video_archiver.retention_playback import PlaybackLogEvidence
from video_archiver.retention_watch_live import (
    collect_user_views, read_playback_log_evidence, scope_watch_evidence,
)


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
    def test_retained_ancestor_playback_protects_reset_userdata(self):
        episode = '12345678123412341234123456789abc'
        season = '12345678123412341234123456789abd'
        views = tuple(CompleteUserView(user, True, {
            episode: UserWatch(user), season: UserWatch(user),
        }) for user in sorted(USERS))
        playback = PlaybackLogEvidence(frozenset({season}), 1, None, None)
        result = scope_watch_evidence((episode, season), views, USERS, playback)
        self.assertIsNotNone(result)
        self.assertFalse(any(row.protected for row in result[0]))
        self.assertTrue(result[1])

    def test_season_ancestor_watch_and_missing_item_hold_scope(self):
        def ancestor_fetch(url, _headers):
            user = url.split('/Users/')[1].split('/')[0]
            requested = parse_qs(urlparse(url).query)['Ids'][0].split(',')
            return 200, {'Items': [
                {'Id': value, 'UserData': {
                    'Played': user == 'a' and value == 'season',
                    'PlayCount': 1 if user == 'a' and value == 'season' else 0,
                    'PlaybackPositionTicks': 0, 'IsFavorite': False,
                }} for value in requested if not (user == 'b' and value == 'hidden')
            ]}
        views = collect_user_views(('episode', 'season', 'series', 'hidden'),
                                   user_ids=USERS, jellyfin_url='http://jellyfin.invalid',
                                   jellyfin_api_key='fixture', fetch=ancestor_fetch)
        playback = PlaybackLogEvidence(frozenset(), 1, None, None)
        protected = scope_watch_evidence(('episode', 'season', 'series'), views, USERS, playback)
        self.assertIsNotNone(protected)
        self.assertTrue(protected[0][0].protected)
        self.assertIsNone(scope_watch_evidence(('episode', 'season', 'hidden'), views, USERS, playback))

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

    def test_retained_playback_logs_protect_reset_userdata(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'jf.db'
            with sqlite3.connect(path) as db:
                db.executescript('''
                    CREATE TABLE ActivityLogs(ItemId TEXT,UserId TEXT,DateCreated TEXT,Type TEXT);
                    INSERT INTO ActivityLogs VALUES
                      ('12345678-1234-1234-1234-123456789abc','user-a','2026-08-03','VideoPlayback'),
                      ('12345678123412341234123456789abc','user-a','2026-08-04','VideoPlaybackStopped');
                ''')
            evidence = read_playback_log_evidence(path)
            self.assertEqual(evidence.event_count, 2)
            self.assertEqual(len(evidence.item_ids), 1)

    def test_missing_log_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'jf.db'
            with sqlite3.connect(path) as db:
                db.executescript('''
                    CREATE TABLE ActivityLogs(ItemId TEXT,UserId TEXT,DateCreated TEXT,Type TEXT);
                    INSERT INTO ActivityLogs VALUES (NULL,'user-a','2026-08-03','VideoPlayback');
                ''')
            with self.assertRaisesRegex(RuntimeError, 'missing identity'):
                read_playback_log_evidence(path)
