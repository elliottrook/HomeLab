"""HP-only, existing-session, read-only Jellyfin playlist adapter.

Credentials are used in memory only, never returned, logged, copied or placed
in artwork/plugin URLs. This class has no POST/DELETE/account mutation route.
"""
import json,platform,re,hashlib
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
from music_playlists import PlaylistUnavailable,server_id
from music_playlist_save import PlaylistSaveUnavailable


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


class PlaylistReader:
    def __init__(self,path):
        if platform.node()!='AsterTV':raise PlaylistUnavailable('hp-only-playlist-reader')
        try:
            servers=json.loads(Path(path).read_text())['Servers']
            if len(servers)!=1:raise ValueError()
            server=servers[0];self.base=server['address'].rstrip('/');parsed=urlsplit(self.base)
            if parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError()
            if not (parsed.scheme=='https' and parsed.hostname and parsed.hostname.endswith('.elliottrook.com')
                    or parsed.scheme=='http' and re.fullmatch(r'192\.168\.\d{1,3}\.\d{1,3}',parsed.hostname or '')):
                raise ValueError()
            self.user_id=server_id(server['UserId']);token=server['AccessToken']
            if not isinstance(token,str) or not 1<=len(token)<=4096 or any(ord(c)<32 for c in token):raise ValueError()
            self.authorization='MediaBrowser Client="Aster Music Lab", Device="AsterTV", Version="0.1.0", UserId='+json.dumps(self.user_id)+', Token='+json.dumps(token)
            self.opener=build_opener(NoRedirect)
        except Exception:raise PlaylistUnavailable('existing-jellyfin-session-unavailable') from None

    def _get(self,path):
        allowed='/Users/'+self.user_id+'/Items?IncludeItemTypes=Playlist&Recursive=true&Limit=1000'
        if path!=allowed and not re.fullmatch(r'/Playlists/[0-9a-f]{32}',path) and not re.fullmatch('/Users/'+self.user_id+r'/Items/[0-9a-f]{32}',path):
            raise PlaylistUnavailable('playlist-read-route-denied')
        try:
            request=Request(self.base+path,method='GET',headers={'Authorization':self.authorization,'Accept':'application/json'})
            with self.opener.open(request,timeout=15) as response:
                if response.status!=200:raise ValueError()
                raw=response.read(4_000_001)
                if len(raw)>4_000_000:raise ValueError()
                return json.loads(raw)
        except Exception:raise PlaylistUnavailable('jellyfin-playlist-read-unavailable') from None

    def list_playlists(self):
        return self._get('/Users/'+self.user_id+'/Items?IncludeItemTypes=Playlist&Recursive=true&Limit=1000')

    def playlist_details(self,identity):
        return self._get('/Playlists/'+server_id(identity))

    def playlist_metadata(self,identity):
        return self._get('/Users/'+self.user_id+'/Items/'+server_id(identity))


class PlaylistCreator(PlaylistReader):
    """Explicitly approved HP create-only path; no update/delete/admin routes."""
    APPROVED_IDENTITY='9db33799226c6f3eb50dcd6e002ce5cc26eebd59aa7f41cb04ae8431a417b625'
    def __init__(self,path):
        super().__init__(path)
        if hashlib.sha256((self.base+'|'+self.user_id).encode()).hexdigest()!=self.APPROVED_IDENTITY:
            raise PlaylistSaveUnavailable('playlist-saving-identity-changed')

    def __call__(self,method,path,body):
        if (method!='POST' or path!='/Playlists' or not isinstance(body,dict)
                or set(body)!={'Name','UserId','Ids','MediaType','IsPublic'}
                or body['UserId']!=self.user_id or body['IsPublic'] is not False
                or body['MediaType']!='Audio' or not isinstance(body['Name'],str)
                or not 1<=len(body['Name'].strip())<=100
                or any(ord(c)<32 or ord(c)==127 for c in body['Name'])
                or not isinstance(body['Ids'],list) or not 1<=len(body['Ids'])<=20000):
            raise PlaylistSaveUnavailable('playlist-create-route-denied')
        for identity in body['Ids']:server_id(identity)
        try:
            request=Request(self.base+'/Playlists',method='POST',data=json.dumps(body).encode(),
                headers={'Authorization':self.authorization,'Content-Type':'application/json','Accept':'application/json'})
            with self.opener.open(request,timeout=15) as response:
                if response.status!=200:raise ValueError()
                raw=response.read(1_000_001)
                if len(raw)>1_000_000:raise ValueError()
                return json.loads(raw)
        except Exception:raise PlaylistSaveUnavailable('playlist-create-uncertain') from None
