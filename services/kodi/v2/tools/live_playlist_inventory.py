"""HP-only read-only playlist shape inventory; never exports paths/tokens."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import importlib.util,json,os,sys,time,sqlite3
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import xbmc,xbmcgui,xbmcvfs
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/skin.asterhome/tools')
import music_data


def rpc(method,params):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    _require(('error' not in result), ('native-read-failed'))
    return result['result']


_require((not rpc('Player.GetActivePlayers',{})), ('native-check-failed'))
rows,total=music_data.playlist_query(xbmc,xbmcgui,xbmcvfs)
summary=[]
connection=sqlite3.connect('file:/storage/.kodi/userdata/Database/jellyfin.db?mode=ro',uri=True)
mapping_types=connection.execute('SELECT media_type,jellyfin_type,count(*) FROM jellyfin GROUP BY media_type,jellyfin_type').fetchall()
connection.close()
for row in rows:
    # Resolve through the installed add-on's existing signed-in authority.
    # Only retain aggregate shapes, never file/plugin URLs, titles or tokens.
    result=rpc('Files.GetDirectory',dict(directory=row['file'],media='music',properties=['title','duration']))
    entries=result.get('files',[])
    summary.append(dict(source=row['source'],reported_total=result.get('limits',{}).get('total'),
        returned=len(entries),indexed_songs=sum(e.get('type')=='song' and type(e.get('id')) is int and e['id']>0 for e in entries),
        file_entries=sum(e.get('filetype')=='file' for e in entries),
        fields=sorted({k for e in entries for k in e if k not in ('file','thumbnail','art')}),
        schemes=sorted({urlsplit(e.get('file','')).scheme for e in entries}),
        query_fields=sorted({k for e in entries for k in parse_qs(urlsplit(e.get('file','')).query)})))
root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
p=root/('playlist-inventory-'+str(time.time_ns())+'.json')
p.write_text(json.dumps(dict(total=total,playlists=summary,mapping_types=mapping_types,read_only=True,paths_retained=False)))
p.chmod(0o600)
