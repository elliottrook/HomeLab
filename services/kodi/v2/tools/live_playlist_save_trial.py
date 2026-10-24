"""ONE approved HP-origin private shared-playlist create/verify/delete trial.

Existing administrator session explicitly disclosed/approved for this trial.
No admin key, identity change, overwrite, general delete or uncertain retry.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import hashlib,json,os,sqlite3,sys,time
from pathlib import Path
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError

_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
sys.path.insert(0,'/storage/.aster-staging/playlist-save-test')
from music_queue import QueueSnapshot
from music_playlist_save import plan_save,create_once,verify_created,uuid

ROOT=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
run=ROOT/('shared-save-'+str(time.time_ns()));run.mkdir(mode=0o700)
def private(path,data):
    with path.open('x') as output:
        json.dump(data,output,sort_keys=True);output.flush();os.fsync(output.fileno())
    path.chmod(0o600)


servers=json.loads(Path('/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/data.json').read_text())['Servers']
_require((len(servers)==1), ('ambiguous-server'))
s=servers[0];base=s['address'].rstrip('/');user=uuid(s['UserId'])
_require((hashlib.sha256((base+'|'+s['UserId']).encode()).hexdigest()=='9db33799226c6f3eb50dcd6e002ce5cc26eebd59aa7f41cb04ae8431a417b625'), ('identity-changed'))
authorization='MediaBrowser Client="Aster Music Lab", Device="AsterTV", Version="0.1.0", UserId='+json.dumps(user)+', Token='+json.dumps(s['AccessToken'])
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
opener=build_opener(NoRedirect)
created=None;create_requested=False;delete_requested=False;verified=False
def request(method,path,body=None):
    global create_requested,delete_requested
    if method=='POST':
        _require((path=='/Playlists' and not create_requested), ('native-check-failed'))
        _require((body==plan.payload()), ('native-check-failed'))
        create_requested=True
    elif method=='DELETE':
        _require((verified and created and created not in plan.existing_ids and not delete_requested), ('native-check-failed'))
        _require((path=='/Items/'+created and body is None), ('native-check-failed'))
        delete_requested=True
    else:
        _require((method=='GET' and (path.startswith('/Users/'+user) or path.startswith('/Playlists/'))), ('native-check-failed'))
    encoded=json.dumps(body).encode() if body is not None else None
    req=Request(base+path,data=encoded,method=method,headers={'Authorization':authorization,'Content-Type':'application/json','Accept':'application/json'})
    try:
        with opener.open(req,timeout=20) as response:
            _require((response.status in (200,204)), ('native-check-failed'))
            data=response.read(4_000_000)
            return json.loads(data) if data else None
    except HTTPError as error:raise RuntimeError('playlist-http-'+str(error.code)) from None
    except Exception:raise RuntimeError('playlist-transport-or-response-uncertain') from None


def inventory():
    listing=request('GET','/Users/'+user+'/Items?IncludeItemTypes=Playlist&Recursive=true&Limit=1000')
    _require((len(listing.get('Items',[]))==listing.get('TotalRecordCount')), ('truncated-inventory'))
    records=[]
    for item in listing['Items']:
        identity=uuid(item['Id'])
        records.append(dict(Id=identity,Name=item['Name'],Type=item['Type'],MediaType=item.get('MediaType'),
                            details=request('GET','/Playlists/'+identity)))
    records.sort(key=lambda row:row['Id'])
    _require((len({r['Id'] for r in records})==len(records)), ('native-check-failed'))
    return records


account=request('GET','/Users/'+user)
_require((uuid(account['Id'])==user and account['Policy']['IsAdministrator'] is True and account['Policy']['IsDisabled'] is False), ('native-check-failed'))
before=inventory();_require((len(before)==16), ('native-check-failed'))
private(run/'existing-playlists-before.json',before)
_require((json.loads((run/'existing-playlists-before.json').read_text())==before), ('native-check-failed'))
selected=tuple(json.loads(Path('/storage/.aster-checkpoints/aster-music-live-trial-20261023/trial-selection.json').read_text())['song_ids'])
_require((len(selected)==len(set(selected))==3), ('native-check-failed'))
queue=QueueSnapshot((selected[0],selected[1],selected[0]),None)
connection=sqlite3.connect('file:/storage/.kodi/userdata/Database/jellyfin.db?mode=ro',uri=True)
mapping={}
try:
    for identity in selected:
        rows=connection.execute('SELECT jellyfin_id FROM jellyfin WHERE kodi_id=? AND media_type=?',(identity,'song')).fetchall()
        _require((len(rows)==1), ('ambiguous-song-mapping'))
        mapping[identity]=uuid(rows[0][0])
finally:connection.close()
plan=plan_save(queue,'Aster lab verification '+str(time.time_ns()),mapping,user,before)
journal_count=0
def journal(record):
    global journal_count
    journal_count+=1;private(run/('journal-'+str(journal_count)+'.json'),record)


created=create_once(request,plan,queue,confirmed=True,journal=journal)
metadata=request('GET','/Users/'+user+'/Items/'+created)
details=request('GET','/Playlists/'+created)
private(run/'created-playlist.json',dict(Id=created,metadata={k:metadata.get(k) for k in ('Id','Name','Type','MediaType','OwnerId')},details=details))
verified=verify_created(plan,created,metadata,details)
private(run/'verified-before-delete.json',dict(playlist_id=created,verified=verified,existing_ids_unchanged=all(row['Id']!=created for row in before)))
request('DELETE','/Items/'+created)
after=inventory();private(run/'existing-playlists-after.json',after)
_require((before==after), ('existing-playlist-set-or-content-changed'))
result=dict(passed=True,created_private_playlist=True,exact_duplicate_order_verified=True,
            created_test_playlist_deleted=True,existing_playlists_verified=len(before),
            existing_ids_order_sharing_unchanged=True,post_count=1,delete_count=1,
            no_queue_or_player_writes=True,no_new_credentials=True)
private(run/'results.json',result)
print(json.dumps(dict(evidence=run.name,**result)))
