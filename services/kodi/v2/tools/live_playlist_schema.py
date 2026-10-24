"""Read only current server schema fields through the approved existing session."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import json,os
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
servers=json.loads(Path('/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/data.json').read_text())['Servers']
_require((len(servers)==1), ('native-check-failed'))
s=servers[0];base=s['address'].rstrip('/')
authorization='MediaBrowser Client="Aster Music Lab", Device="AsterTV", Version="0.1.0", UserId='+json.dumps(s['UserId'])+', Token='+json.dumps(s['AccessToken'])
opener=build_opener(NoRedirect)
def get(path):
    try:
        with opener.open(Request(base+path,headers={'Authorization':authorization}),timeout=15) as response:
            return json.loads(response.read(16_000_000))
    except Exception:raise RuntimeError('schema-read-unavailable') from None
info=get('/System/Info/Public');schema=get('/api-docs/openapi.json')
schemas=schema.get('components',{}).get('schemas',{})
print(json.dumps(dict(version=info.get('Version'),
    create=schemas.get('CreatePlaylistDto',{}),
    playlist=schemas.get('PlaylistDto',{}),
    create_path=schema['paths'].get('/Playlists',{}).get('post',{}),
    read_path=schema['paths'].get('/Playlists/{playlistId}',{}).get('get',{})),ensure_ascii=False))
