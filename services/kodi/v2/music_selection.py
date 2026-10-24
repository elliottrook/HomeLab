"""Path-free, twice-verified single-song selection for the Music player."""
from dataclasses import dataclass
from music_album import AlbumTrack


class SelectionUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class SongSelection:
    tracks: tuple
    kind: str = 'song'
    disc_numbers_available: bool = False

    @property
    def album_id(self):return 'song-'+str(self.tracks[0].song_id)

    @property
    def song_ids(self):return tuple(t.song_id for t in self.tracks)


def read_song(rpc,identity,expected):
    if (type(identity) is not int or identity<1 or not isinstance(expected,dict)
            or expected.get('songid')!=identity):
        raise SelectionUnavailable('invalid-song-selection')
    def read():
        try:
            result=rpc('AudioLibrary.GetSongDetails',dict(songid=identity,properties=['albumid','duration']))
        except Exception:raise SelectionUnavailable('song-read-failed') from None
        row=result.get('songdetails') if isinstance(result,dict) else None
        if (not isinstance(row,dict) or type(row.get('songid')) is not int or row['songid']!=identity
                or not isinstance(row.get('label'),str) or type(row.get('duration')) is not int
                or row['duration']<0 or type(row.get('albumid')) is not int or row['albumid']<0):
            raise SelectionUnavailable('song-unavailable')
        if row['label']!=expected.get('label') or row['albumid']!=expected.get('albumid',0):
            raise SelectionUnavailable('song-selection-stale')
        return SongSelection((AlbumTrack(identity,0,1,row['label'],row['duration']),))
    one,two=read(),read()
    if one!=two:raise SelectionUnavailable('song-changed-during-verification')
    return two
