import copy
import unittest
from music_selection import SelectionUnavailable,read_song


class SongSelectionTests(unittest.TestCase):
    def setUp(self):
        self.expected=dict(songid=7,label='Song',albumid=2)
        self.row=dict(songid=7,label='Song',albumid=2,duration=123,file='private-path')
        self.calls=[]
    def rpc(self,method,params):
        self.calls.append((method,params));return dict(songdetails=copy.deepcopy(self.row))
    def test_single_song_needs_no_album_track_tags_and_never_requests_paths(self):
        selection=read_song(self.rpc,7,self.expected)
        self.assertEqual(selection.song_ids,(7,))
        self.assertEqual(selection.album_id,'song-7')
        self.assertEqual(selection.tracks[0].duration,123)
        self.assertEqual(len(self.calls),2)
        self.assertTrue(all(m=='AudioLibrary.GetSongDetails' and p['properties']==['albumid','duration'] for m,p in self.calls))
        self.assertNotIn('private-path',repr(selection))
    def test_missing_metadata_and_foreign_identity_fail_closed(self):
        for key,value in (('songid',True),('songid',8),('duration',-1),('duration',True),('albumid',None),('label',None)):
            with self.subTest(field=key,value=value):
                self.row[key]=value
                with self.assertRaises(SelectionUnavailable):read_song(self.rpc,7,self.expected)
                self.setUp()
    def test_stale_title_or_album_refuses_selection(self):
        for key,value in (('label','Renamed'),('albumid',3)):
            self.row[key]=value
            with self.assertRaisesRegex(SelectionUnavailable,'stale'):read_song(self.rpc,7,self.expected)
            self.setUp()
    def test_changing_duration_between_reads_is_not_accepted(self):
        def rpc(method,params):
            result=self.rpc(method,params);self.row['duration']+=1;return result
        with self.assertRaisesRegex(SelectionUnavailable,'changed'):read_song(rpc,7,self.expected)
    def test_transport_errors_are_sanitized(self):
        def rpc(*args):raise RuntimeError('secret-private-path')
        with self.assertRaisesRegex(SelectionUnavailable,'^song-read-failed$'):read_song(rpc,7,self.expected)
    def test_invalid_input_never_reads(self):
        for identity in (True,0,'7'):
            with self.assertRaises(SelectionUnavailable):read_song(self.rpc,identity,self.expected)
        self.assertFalse(self.calls)
