"""HP read-only playlist diagnostics; export counts/codes, never URLs or names."""
import importlib.util,json,os,sys,time
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import xbmc,xbmcgui,xbmcvfs
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
sys.path.insert(0,'/storage/.kodi/addons/skin.asterhome/tools')
from aster_v2_music import selection_key
from music_catalogue import read_catalogue
from music_playlists import read_playlists,read_playlist,indexed_mapping,PlaylistUnavailable
from music_jellyfin import PlaylistReader
def rpc(method,params):
    if not method.startswith('AudioLibrary.Get'):raise RuntimeError('read-only')
    data=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    if 'error' in data:raise RuntimeError('rpc-read-failed')
    return data.get('result',{})
result=dict(window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId())
try:
    reader=PlaylistReader(xbmcvfs.translatePath('special://profile/addon_data/plugin.video.jellyfin/data.json'))
    rows=read_playlists(reader);result['server_playlist_count']=len(rows)
    catalogue=read_catalogue(rpc);result['indexed_song_count']=len(catalogue.songs)
    outcomes=[]
    for row in rows:
        try:
            selection=read_playlist(reader,row['playlistid'],rows,catalogue,
                lambda ids:indexed_mapping(xbmcvfs.translatePath('special://profile/Database/jellyfin.db'),ids))
            outcomes.append(dict(ok=True,tracks=len(selection.tracks)))
        except PlaylistUnavailable as error:outcomes.append(dict(ok=False,code=str(error)))
    result['server_selection_checks']=outcomes
    spec=importlib.util.spec_from_file_location('aster_music_front_probe','/storage/.kodi/addons/skin.asterhome/tools/music_data.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    front,total=module.playlist_query(xbmc,xbmcgui,xbmcvfs)
    result['front_count']=len(front);checks=[]
    for row in front:
        path=row.get('file','');parts=urlsplit(path);q=parse_qs(parts.query)
        try:key=selection_key('playlists','',path);checks.append(dict(valid=key is not None,mode=q.get('mode'),type=q.get('type'),keys=sorted(q)))
        except ValueError:checks.append(dict(valid=False,mode=q.get('mode'),type=q.get('type'),keys=sorted(q)))
    result['front_route_checks']=checks;result['ok']=True
except Exception as error:
    result.update(ok=False,error=type(error).__name__,code=str(error) if isinstance(error,PlaylistUnavailable) else 'read-unavailable')
directory=Path('/storage/.aster-checkpoints/aster-feedback-20261024');directory.mkdir(mode=0o700,exist_ok=True)
path=directory/('probe-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
