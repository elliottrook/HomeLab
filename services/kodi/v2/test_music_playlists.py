import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
from music_playlists import PlaylistUnavailable,indexed_mapping,read_playlists,read_playlist
from music_jellyfin import PlaylistReader,NoRedirect

ONE='1'*32;TWO='2'*32;LIST='3'*32


class FakeAPI:
    def __init__(self):
        self.rows=[dict(Id=LIST,Name='Playlist',Type='Playlist',MediaType='Audio')]
        self.ids=[ONE,TWO,ONE]
    def list_playlists(self):return dict(Items=copy.deepcopy(self.rows),TotalRecordCount=len(self.rows))
    def playlist_details(self,identity):return dict(ItemIds=list(self.ids))


class PlaylistReadTests(unittest.TestCase):
    def setUp(self):
        self.api=FakeAPI();self.cat=SimpleNamespace(songs={1:dict(label='One'),2:dict(label='Two')})
        self.links={ONE:1,TWO:2}
    def selection(self):
        return read_playlist(self.api,LIST,read_playlists(self.api),self.cat,lambda ids:{i:self.links[i] for i in set(ids) if i in self.links})
    def test_exact_saved_order_duplicates_and_unknown_duration(self):
        selected=self.selection();self.assertEqual(selected.song_ids,(1,2,1))
        self.assertEqual([r.track for r in selected.tracks],[1,2,3])
        self.assertTrue(all(r.duration==0 for r in selected.tracks))
        self.assertNotIn('file',repr(selected))
    def test_empty_playlist_is_truthful_not_a_placeholder(self):
        self.api.ids=[];self.assertEqual(self.selection().song_ids,())
    def test_no_unindexed_song_is_silently_omitted(self):
        self.links.pop(TWO)
        with self.assertRaisesRegex(PlaylistUnavailable,'not-indexed'):self.selection()
    def test_stale_or_truncated_lists_are_not_published(self):
        self.api.list_playlists=lambda:dict(Items=[],TotalRecordCount=16)
        with self.assertRaisesRegex(PlaylistUnavailable,'incomplete'):read_playlists(self.api)
        self.api=FakeAPI();count=0
        def listing():
            nonlocal count
            result=FakeAPI.list_playlists(self.api);result['Items'][0]['Name']=str(count);count+=1;return result
        self.api.list_playlists=listing
        with self.assertRaisesRegex(PlaylistUnavailable,'changed'):read_playlists(self.api)
    def test_changing_order_refuses_selection(self):
        def details(identity):
            result=dict(ItemIds=list(self.api.ids));self.api.ids.reverse();self.api.ids.append(TWO);return result
        self.api.playlist_details=details
        with self.assertRaisesRegex(PlaylistUnavailable,'changed'):self.selection()
    def test_foreign_playlist_is_not_read(self):
        self.api.playlist_details=Mock()
        with self.assertRaises(PlaylistUnavailable):read_playlist(self.api,ONE,read_playlists(self.api),self.cat,lambda ids:{})
        self.api.playlist_details.assert_not_called()
    def test_mapping_is_exact_read_only_and_rejects_ambiguous_or_missing_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'jellyfin.db';c=sqlite3.connect(path)
            c.execute('CREATE TABLE jellyfin(jellyfin_id TEXT,kodi_id INTEGER,media_type TEXT)')
            c.executemany('INSERT INTO jellyfin VALUES(?,?,?)',[(ONE,1,'song'),(TWO,2,'song')]);c.commit();c.close()
            before=path.read_bytes();self.assertEqual(indexed_mapping(path,[ONE,TWO,ONE]),self.links)
            self.assertEqual(path.read_bytes(),before)
            with self.assertRaises(PlaylistUnavailable):indexed_mapping(path,[LIST])
            c=sqlite3.connect(path);c.execute('INSERT INTO jellyfin VALUES(?,?,?)',(ONE,9,'song'));c.commit();c.close()
            with self.assertRaises(PlaylistUnavailable):indexed_mapping(path,[ONE])
    def test_reader_refuses_foreign_host_credentials_and_arbitrary_routes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'data.json';path.write_text(json.dumps(dict(Servers=[dict(address='http://192.168.20.1:8096',UserId=ONE,AccessToken='private-test-token')])))
            with patch('music_jellyfin.platform.node',return_value='Production'):
                with self.assertRaisesRegex(PlaylistUnavailable,'hp-only'):PlaylistReader(path)
            with patch('music_jellyfin.platform.node',return_value='AsterTV'):
                reader=PlaylistReader(path);reader.opener=Mock()
                with self.assertRaisesRegex(PlaylistUnavailable,'route-denied'):reader._get('/Users')
                reader.opener.open.assert_not_called()
            path.write_text(json.dumps(dict(Servers=[dict(address='https://evil.example',UserId=ONE,AccessToken='private-test-token')])))
            with patch('music_jellyfin.platform.node',return_value='AsterTV'):
                with self.assertRaises(PlaylistUnavailable):PlaylistReader(path)
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://elsewhere.example'))
