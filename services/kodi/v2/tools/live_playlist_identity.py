"""HP read-only current-user/playlist permission preflight, no secret output.

Uses only the add-on's one existing server/user session and refuses redirects.
Never creates a token, user, playlist or HTTP trust exception.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import hashlib,json,os,re,time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


servers=json.loads(Path('/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/data.json').read_text())['Servers']
_require((len(servers)==1), ('ambiguous-server'))
server=servers[0];base=server.get('address','').rstrip('/');parsed=urlsplit(base)
_require((not parsed.username and not parsed.password and not parsed.query and not parsed.fragment), ('native-check-failed'))
_require((parsed.scheme=='https' and parsed.hostname and parsed.hostname.endswith('.elliottrook.com')
        or parsed.scheme=='http' and re.fullmatch(r'192\.168\.\d{1,3}\.\d{1,3}',parsed.hostname or '')), ('unexpected-server-origin'))
user=server.get('UserId');token=server.get('AccessToken')
_require((isinstance(user,str) and re.fullmatch(r'[a-fA-F0-9]{32}',user) and isinstance(token,str) and token), ('native-check-failed'))
opener=build_opener(NoRedirect)
def get(path):
    # Match the installed Kodi client's MediaBrowser authorization scheme;
    # do not assume a proxy accepts the legacy X-Emby-Token header.
    authorization='MediaBrowser Client="Aster Music Lab", Device="AsterTV", Version="0.1.0", UserId='+json.dumps(user)+', Token='+json.dumps(token)
    request=Request(base+path,headers={'Authorization':authorization,'Accept':'application/json'})
    try:
        with opener.open(request,timeout=15) as response:
            _require((response.status==200), ('native-check-failed'))
            return json.loads(response.read(2_000_000))
    except HTTPError as error:raise RuntimeError('existing-session-http-'+str(error.code)) from None
    except URLError as error:raise RuntimeError('existing-session-transport-'+type(error.reason).__name__) from None
    except Exception:raise RuntimeError('existing-session-response-unavailable') from None


account=get('/Users/'+user)
_require((account.get('Id','').replace('-','').lower()==user.lower()), ('identity-mismatch'))
policy=account.get('Policy',{})
items=get('/Users/'+user+'/Items?IncludeItemTypes=Playlist&Recursive=true&Limit=1000')
_require((isinstance(items.get('Items'),list) and len(items['Items'])==items.get('TotalRecordCount')), ('playlist-list-truncated'))
summary=dict(read_only=True,existing_session_only=True,redirects_refused=True,
    identity_sha256=hashlib.sha256((base+'|'+user).encode()).hexdigest(),
    administrator=policy.get('IsAdministrator'),disabled=policy.get('IsDisabled'),
    enable_shared_device_control=policy.get('EnableSharedDeviceControl'),
    server_playlists=len(items['Items']),audio_playlists=sum(i.get('MediaType')=='Audio' for i in items['Items']))
root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
p=root/('playlist-identity-'+str(time.time_ns())+'.json')
p.write_text(json.dumps(summary));p.chmod(0o600)
print(json.dumps(summary))
