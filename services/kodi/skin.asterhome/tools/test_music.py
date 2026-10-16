"""Synthetic checks for Aster Music's local-library screens."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from music_data import (music_row, music_query, playlist_query, album_tracks,
                        play_album, player_tracks, play_selection, PAGES, MUSIC_PLAYER)


ROOT = Path(__file__).resolve().parents[1]


class MusicTests(unittest.TestCase):
    def test_five_music_windows_share_layout_and_indexed_sources(self):
        layout = ET.parse(ROOT / '1080i/IncludesMusic.xml')
        self.assertIsNotNone(layout.find('.//control[@id="500"]'))
        self.assertIsNotNone(layout.find('.//control[@id="301"]'))
        for page, identifier in PAGES.items():
            source = ROOT / f'1080i/custom_{identifier - 10000}_{"music" if page == "home" else page}.xml'
            root = ET.parse(source)
            self.assertEqual(int(root.getroot().get('id')) + 10000, identifier)
            self.assertEqual(root.find('.//param[@name="page"]').get('value'), page)

    def test_queries_are_bounded_and_artist_filter_is_local(self):
        calls = []

        class FakeKodi:
            def executeJSONRPC(self, payload):
                import json
                request = json.loads(payload)
                calls.append(request)
                return json.dumps({'result': {'albums': [], 'limits': {'total': 0}}})

        rows, total = music_query(FakeKodi(), 'albums', '42')
        self.assertEqual((rows, total), ([], 0))
        self.assertEqual(calls[0]['params']['filter'], {'artistid': 42})
        self.assertEqual(calls[0]['params']['limits']['end'], 500)
        music_query(FakeKodi(), 'home')
        self.assertEqual(calls[1]['method'], 'AudioLibrary.GetRecentlyAddedAlbums')
        music_query(FakeKodi(), 'songs', query='Queen')
        self.assertEqual(calls[2]['params']['filter'],
                         {'or': [{'field': field, 'operator': 'contains', 'value': 'Queen'}
                                 for field in ('title', 'artist', 'album')]})

    def test_metadata_is_truthful(self):
        album = music_row('albums', {'albumid': 7, 'label': 'Synthetic Album',
                                     'artist': ['Example Artist'], 'year': 2024})
        self.assertEqual(album['detail'], 'Example Artist · 2024')
        self.assertEqual(album['id'], 7)
        song = music_row('songs', {'songid': 9, 'label': 'Synthetic Song',
                                   'artist': ['Example Artist'], 'album': 'Synthetic Album',
                                   'duration': 185})
        self.assertIn('3:05', song['summary'])
        song['thumb'] = ''
        self.assertEqual(song['fanart'], '')
        with_art = music_row('songs', {'songid': 10, 'label': 'Synthetic Song',
                                       'art': {'album.thumb': 'image://cover'}})
        self.assertEqual(with_art['thumb'], 'image://cover')

    def test_playlist_discovery_is_local_and_bounded(self):
        import json
        class FakeVfs:
            def listdir(self, path):
                self.path = path
                return [], ['Listen.m3u', 'Mix.xsp', 'cover.png', 'Jams.M3U8']

        vfs = FakeVfs()
        class FakeWindow:
            def getProperty(self, name):
                return {'Jellyfin.wnodes.total': '1',
                        'Jellyfin.wnodes.0.type': 'playlists',
                        'Jellyfin.wnodes.0.content':
                        'plugin://plugin.video.jellyfin/?mode=browse&type=playlists&id=abc'}.get(name, '')

        class FakeGui:
            Window = staticmethod(lambda _id: FakeWindow())

        class FakeKodi:
            def executeJSONRPC(self, request):
                self.request = json.loads(request)
                return json.dumps({'result': {'files': [
                    {'label': 'Road trip', 'file':
                     'plugin://plugin.video.jellyfin/?mode=browse&type=playlists&id=abc&folder=123',
                     'thumbnail': 'image://road-trip'},
                    {'label': 'Wrong item', 'file': 'https://example.invalid/item'}]}})

        kodi = FakeKodi()
        rows, total = playlist_query(kodi, FakeGui(), vfs)
        self.assertEqual(vfs.path, 'special://musicplaylists/')
        self.assertEqual(total, 4)
        self.assertEqual([row['label'] for row in rows], ['Jams', 'Listen', 'Mix', 'Road trip'])
        self.assertEqual(kodi.request['method'], 'Files.GetDirectory')
        self.assertEqual(music_row('playlists', rows[0])['file'],
                         'special://musicplaylists/Jams.M3U8')

    def test_album_player_loads_ordered_tracks_and_opens_selected_position(self):
        import json
        calls = []

        class FakeKodi:
            def executeJSONRPC(self, payload):
                request = json.loads(payload)
                calls.append(request)
                result = {'songs': [{'songid': 11, 'label': 'First'},
                                    {'songid': 12, 'label': 'Second'}]} if request['method'] == 'AudioLibrary.GetSongs' else 'OK'
                return json.dumps({'result': result})

        kodi = FakeKodi()
        self.assertEqual(len(album_tracks(kodi, 42)), 2)
        play_album(kodi, 42, 1)
        self.assertEqual(calls[-3]['method'], 'Playlist.Clear')
        self.assertEqual(calls[-2]['params']['item'], [{'songid': 11}, {'songid': 12}])
        self.assertEqual(calls[-1]['params']['item'], {'playlistid': 0, 'position': 1})
        with self.assertRaisesRegex(ValueError, 'no longer in this album'):
            play_album(kodi, 42, 3)

    def test_album_player_is_a_separate_two_column_page(self):
        player = ET.parse(ROOT / '1080i/custom_1121_albumplayer.xml').getroot()
        self.assertEqual(int(player.get('id')) + 10000, MUSIC_PLAYER)
        self.assertIsNotNone(player.find('.//control[@id="50"]'))
        self.assertIn('AsterMusic.Cover', ET.tostring(player, encoding='unicode'))
        self.assertIn('music-player,track', ET.tostring(player, encoding='unicode'))
        self.assertIn('Open album', (ROOT / '1080i/custom_1114_albums.xml').read_text())
        self.assertIn('Open song', (ROOT / '1080i/custom_1116_songs.xml').read_text())
        tiles = (ROOT / '1080i/IncludesMusic.xml').read_text()
        self.assertIn('<onclick>RunScript(special://skin/tools/music_data.py,$PARAM[page],open)</onclick>', tiles)
        self.assertIn('Open playlist', (ROOT / '1080i/custom_1117_playlists.xml').read_text())

    def test_song_and_playlist_player_sources_and_queue(self):
        import json
        calls = []

        class FakeKodi:
            def executeJSONRPC(self, payload):
                request = json.loads(payload)
                calls.append(request)
                if request['method'] == 'AudioLibrary.GetSongDetails':
                    return json.dumps({'result': {'songdetails': {'songid': 8,
                                                                  'label': 'One song'}}})
                if request['method'] == 'Files.GetDirectory':
                    return json.dumps({'result': {'files': [
                        {'filetype': 'file', 'label': 'First', 'file': 'plugin://plugin.video.jellyfin/?mode=play&id=1'},
                        {'filetype': 'directory', 'label': 'Skip', 'file': 'plugin://plugin.video.jellyfin/?mode=browse&id=2'}]}})
                return json.dumps({'result': 'OK'})

        kodi = FakeKodi()
        song = player_tracks(kodi, 'song', '8')
        self.assertEqual(song[0]['label'], 'One song')
        playlist = player_tracks(kodi, 'playlist', '',
                                 'plugin://plugin.video.jellyfin/?mode=browse&type=playlists&folder=123')
        self.assertEqual(len(playlist), 1)
        play_selection(kodi, 'playlist', '', '', playlist)
        self.assertEqual(calls[-2]['method'], 'Playlist.Add')
        self.assertEqual(calls[-1]['method'], 'Player.Open')
        play_selection(kodi, 'song', '8', '', song)
        self.assertEqual(calls[-1]['params']['item'], {'songid': 8})

    def test_recent_is_landing_not_a_pill_and_music_tiles_are_square(self):
        xml = (ROOT / '1080i/IncludesMusic.xml').read_text()
        self.assertIn('value="home"', (ROOT / '1080i/custom_1113_music.xml').read_text())
        self.assertNotIn('<label>Recently Added</label>', xml)
        for name in ('Albums', 'Artists', 'Songs', 'Playlists'):
            self.assertIn(f'<label>{name}</label>', xml)
        self.assertNotIn('$INFO[Container(500).ListItem.Art(thumb)]', xml)
        self.assertIn('AsterMusic.HasArt', xml)
        self.assertIn('ui-hero-bottom-fade.png', xml)


if __name__ == '__main__':
    unittest.main()
