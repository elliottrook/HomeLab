"""Read-only, exact-song album cover resolution; never returns a stale cover."""

def song_album_art(rpc, song_id, fallback):
    if type(song_id) is not int or song_id <= 0:return fallback
    try:
        song=rpc('AudioLibrary.GetSongDetails',{'songid':song_id,'properties':['albumid','thumbnail']}).get('songdetails',{})
        if song.get('songid')!=song_id:return fallback
        album_id=song.get('albumid')
        if type(album_id) is int and album_id>0:
            try:
                album=rpc('AudioLibrary.GetAlbumDetails',{'albumid':album_id,'properties':['thumbnail','art']}).get('albumdetails',{})
                if album.get('albumid')==album_id:
                    art=album.get('art') or {}
                    for value in (album.get('thumbnail'),art.get('thumb') if isinstance(art,dict) else None):
                        if isinstance(value,str) and value:return value
            except Exception:pass
        value=song.get('thumbnail')
        return value if isinstance(value,str) and value else fallback
    except Exception:return fallback
