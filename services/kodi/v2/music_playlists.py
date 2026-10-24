"""Exact read-only shared-playlist -> indexed-song selection; never fuzzy-match."""
from dataclasses import dataclass
import sqlite3
from pathlib import Path
from music_album import AlbumTrack
from music_playlist_save import uuid,PlaylistSaveUnavailable


class PlaylistUnavailable(ValueError):
    pass


def server_id(value):
    try:return uuid(value)
    except PlaylistSaveUnavailable:raise PlaylistUnavailable('invalid-playlist-identity') from None


def read_playlists(api,*,include_other=False):
    def read():
        try:result=api.list_playlists()
        except Exception:raise PlaylistUnavailable('playlists-read-failed') from None
        rows=result.get('Items') if isinstance(result,dict) else None
        if (not isinstance(rows,list) or type(result.get('TotalRecordCount')) is not int
                or len(rows)!=result['TotalRecordCount'] or len(rows)>1000):
            raise PlaylistUnavailable('incomplete-playlist-list')
        clean=[];seen=set()
        for row in rows:
            if (not isinstance(row,dict) or not isinstance(row.get('Name'),str)
                    or row.get('Type')!='Playlist'):
                raise PlaylistUnavailable('invalid-playlist-list')
            identity=server_id(row.get('Id'))
            if identity in seen:raise PlaylistUnavailable('invalid-playlist-list')
            seen.add(identity)
            if include_other or row.get('MediaType')=='Audio':clean.append(dict(playlistid=identity,label=row['Name']))
        return sorted(clean,key=lambda r:(r['label'].casefold(),r['playlistid']))
    one,two=read(),read()
    if one!=two:raise PlaylistUnavailable('playlists-changed-during-read')
    return tuple(two)


def indexed_mapping(path,identities):
    requested={server_id(i) for i in identities}
    if len(requested)>20000:raise PlaylistUnavailable('playlist-too-large')
    found={};connection=None
    try:
        connection=sqlite3.connect(Path(path).as_uri()+'?mode=ro',uri=True)
        for identity in requested:
            rows=connection.execute('SELECT kodi_id FROM jellyfin WHERE jellyfin_id=? AND media_type=?',(identity,'song')).fetchall()
            if len(rows)!=1 or type(rows[0][0]) is not int or rows[0][0]<1:
                raise PlaylistUnavailable('playlist-tracks-not-indexed')
            found[identity]=rows[0][0]
        if len(set(found.values()))!=len(found):raise PlaylistUnavailable('ambiguous-playlist-mapping')
    except sqlite3.Error:raise PlaylistUnavailable('playlist-index-unavailable') from None
    finally:
        if connection:connection.close()
    return found


def server_mapping(path,identities):
    requested=set(identities)
    if not 1<=len(requested)<=20000 or any(type(i) is not int or i<1 for i in requested):
        raise PlaylistUnavailable('invalid-queue-identity')
    found={};connection=None
    try:
        connection=sqlite3.connect(Path(path).as_uri()+'?mode=ro',uri=True)
        for identity in requested:
            rows=connection.execute('SELECT jellyfin_id FROM jellyfin WHERE kodi_id=? AND media_type=?',(identity,'song')).fetchall()
            if len(rows)!=1:raise PlaylistUnavailable('queue-song-not-mapped')
            found[identity]=server_id(rows[0][0])
        if len(set(found.values()))!=len(found):raise PlaylistUnavailable('ambiguous-playlist-mapping')
    except sqlite3.Error:raise PlaylistUnavailable('playlist-index-unavailable') from None
    finally:
        if connection:connection.close()
    return found


@dataclass(frozen=True)
class PlaylistSelection:
    playlist_id:str
    tracks:tuple
    kind:str='playlist'
    disc_numbers_available:bool=False
    @property
    def album_id(self):return 'playlist-'+self.playlist_id
    @property
    def song_ids(self):return tuple(t.song_id for t in self.tracks)


def read_playlist(api,identity,known,catalogue,mapping):
    identity=server_id(identity)
    if identity not in {row['playlistid'] for row in known}:raise PlaylistUnavailable('playlist-preview-stale')
    def read():
        try:details=api.playlist_details(identity)
        except Exception:raise PlaylistUnavailable('playlist-read-failed') from None
        ids=details.get('ItemIds') if isinstance(details,dict) else None
        if not isinstance(ids,list) or len(ids)>20000:raise PlaylistUnavailable('incomplete-playlist')
        ids=tuple(server_id(i) for i in ids)
        links=mapping(ids)
        if set(links)!=set(ids) or any(type(i) is not int or i not in catalogue.songs for i in links.values()):
            raise PlaylistUnavailable('playlist-tracks-not-indexed')
        def track(identity,position):
            row=catalogue.songs[identity];duration=row.get('duration')
            return AlbumTrack(identity,0,position,row.get('label','Untitled'),
                duration if type(duration) is int and duration>0 else 0)
        return PlaylistSelection(identity,tuple(track(links[i],n+1) for n,i in enumerate(ids)))
    one,two=read(),read()
    if one!=two:raise PlaylistUnavailable('playlist-changed-during-read')
    return two
