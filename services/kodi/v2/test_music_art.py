import unittest
from unittest.mock import Mock
from music_art import song_album_art

class MusicArtTests(unittest.TestCase):
    def test_album_cover_wins_over_song_or_playlist_art(self):
        rpc=Mock(side_effect=[{'songdetails':{'songid':7,'albumid':3,'thumbnail':'song'}},
                              {'albumdetails':{'albumid':3,'thumbnail':'album'}}])
        self.assertEqual(song_album_art(rpc,7,'missing'),'album')
        self.assertEqual(rpc.call_args.args[1]['albumid'],3)

    def test_album_thumb_art_and_song_fallback(self):
        for album,expected in [({'albumid':3,'art':{'thumb':'cover'}},'cover'),
                               ({'albumid':4,'thumbnail':'wrong'},'song'),({},'song')]:
            rpc=Mock(side_effect=[{'songdetails':{'songid':7,'albumid':3,'thumbnail':'song'}}, {'albumdetails':album}])
            self.assertEqual(song_album_art(rpc,7,'missing'),expected)

    def test_missing_invalid_or_unavailable_metadata_never_keeps_old_cover(self):
        for response in ({},{'songdetails':{'songid':8,'thumbnail':'wrong'}},
                         {'songdetails':{'songid':7,'thumbnail':''}}):
            self.assertEqual(song_album_art(Mock(return_value=response),7,'missing'),'missing')
        self.assertEqual(song_album_art(Mock(side_effect=ValueError()),7,'missing'),'missing')
        rpc=Mock();self.assertEqual(song_album_art(rpc,True,'missing'),'missing');rpc.assert_not_called()

    def test_album_failure_can_use_song_cover(self):
        rpc=Mock(side_effect=[{'songdetails':{'songid':7,'albumid':3,'thumbnail':'song'}},ValueError()])
        self.assertEqual(song_album_art(rpc,7,'missing'),'song')
