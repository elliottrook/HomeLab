"""Exactly one approved HP disposable bookmark trial; no playback or activation."""
import fcntl,hashlib,importlib.util,json,os,secrets,shutil,sys,time,urllib.request
from pathlib import Path
import xbmc,xbmcgui
sys.path[:0]=[str(Path(__file__).resolve().parent),'/storage/.kodi/addons/plugin.audio.asterbooks',
    '/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib']
from books_bookmark_trial import BookmarkTrial,bookmark,project
from books_progress import require,identifier,ProgressUnavailable
from books_progress_reader import Reader
from books_progress_trial import atomic
ACCOUNT='5326816b7ef0f98b2ab17a43d8502a3763947d1bad27f8bd10f6e2ac85bcc206'
BRIDGE='f37d51aec0bb8b48c1d31e9f9c442e4476130630b67a5bdc070af18dfd1a5c67'
SYNC='dd502b6770ec6c0f76e4c2fb4182c54c4b84e4c5162a70e0c0dd2a205a643dd7'
BASE=Path('/storage/.aster-checkpoints/aster-books-bookmark-20261025')
ROOT=BASE/'trial1'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems'),'bookmark-read-only-native')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-read-failed');return reply['result']
def idle():
    return xbmcgui.getCurrentWindowId()==10000 and not rpc('Player.GetActivePlayers') and all(
        rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
require(os.uname().nodename=='AsterTV' and len(sys.argv)==2,'hp-bookmark-mode-required')
mode=sys.argv[1];require(mode in ('inspect','run-approved-one-trial'),'known-bookmark-mode')
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
BASE.mkdir(mode=0o700,parents=True,exist_ok=True)
require(not BASE.is_symlink() and BASE.stat().st_mode&0o077==0,'private-bookmark-base')
result=dict(passed=False,mode=mode,production_changed=False,normal_bookmark_ui_enabled=False);phase='preflight'
try:
    require(idle(),'idle-home-empty-required')
    active=Path('/storage/.aster-checkpoints/aster-books-sync-20261025/active-manifest.json')
    require(sha(active)==SYNC,'accepted-hp-books-overlay-required')
    manifest=json.loads(active.read_text());require(len(manifest['files'])==13,'accepted-thirteen-members')
    installed={r['path']:r['sha256'] for r in manifest['files']}
    for path,digest in installed.items():require(sha(Path('/storage')/path)==digest,'installed-books-drift')
    source=Path('/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib/bridge.py')
    require(sha(source)==BRIDGE,'unchanged-private-bridge-required')
    spec=importlib.util.spec_from_file_location('bookmark_existing_bridge',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    origin,key=module.load_config(Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks/client.json'))
    bridge=module.Bridge(origin,key);del key
    reader=Reader(bridge.upstream)
    def read():
        require(idle(),'playback-changed-do-not-mutate')
        return project(reader,ACCOUNT)
    before=read()
    targets=json.loads(Path('/storage/.aster-checkpoints/aster-books-progress-20261025/trial1/targets-private.json').read_text())
    target=next(t for t in targets if t['kind']=='audiobook');item=identifier(target['item'])
    metadata=bridge.metadata(item)
    require(metadata.get('id')==item and metadata.get('mediaType')=='book','verified-book-only')
    from books_sync_bridge import book_files
    _,spans=book_files(metadata['media']);duration=int(sum(s.duration for s in spans))
    require(duration>30,'verified-book-duration')
    occupied={b.time for b in before.bookmarks if b.item==item}
    choice=None
    for _ in range(10000):
        candidate=secrets.randbelow(duration-2)+1
        if candidate not in occupied:choice=candidate;break
    require(choice is not None,'unoccupied-bookmark-time-required')
    title='Aster lab bookmark '+secrets.token_hex(12)
    if mode=='inspect':
        result.update(passed=True,read_only=True,account_verified=True,existing_bookmark_count=len(before.bookmarks),
            progress_projection_available=True,unoccupied_time_found=True,installed_files_verified=len(installed),idle_empty=True)
    else:
        require(not ROOT.exists(),'one-bookmark-trial-already-started-no-repeat')
        ROOT.mkdir(mode=0o700)
        atomic(ROOT/'before-files.json',installed);atomic(ROOT/'before-state-private.json',before.row())
        for path,digest in installed.items():
            old=Path('/storage')/path;new=ROOT/'before'/path;new.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            require(not old.is_symlink(),'checkpoint-source-linked');shutil.copyfile(old,new);new.chmod(0o600)
            require(sha(new)==digest,'bookmark-checkpoint-failed')
        for name in ('books_bookmark_trial.py',Path(__file__).name):
            old=Path(__file__).parent/name;new=ROOT/name;shutil.copyfile(old,new);new.chmod(0o600)
            require(sha(new)==sha(old),'trial-tool-checkpoint-failed')
        atomic(ROOT/'target-private.json',dict(item=item,time=choice,title=title))
        consumed=dict(create=False,remove=False)
        def create(target,payload):
            require(not consumed['create'] and target==item and payload==dict(time=choice,title=title),'exact-single-create-only')
            require(idle(),'playback-changed-do-not-create');consumed['create']=True
            request=urllib.request.Request(bridge.server_url+'/api/me/item/'+item+'/bookmark',method='POST',
                data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+bridge.api_key,'Content-Type':'application/json'})
            with bridge.opener.open(request,timeout=10) as response:
                require(response.status==200,'bookmark-create-status');raw=response.read(65537)
            require(len(raw)<=65536,'bounded-bookmark-create-response');return json.loads(raw)
        def remove(created):
            require(consumed['create'] and not consumed['remove'],'exact-single-delete-only')
            require((created.item,created.time,created.title)==(item,choice,title),'delete-only-created-bookmark')
            require(bookmark(json.loads((ROOT/'writes/created-private.json').read_text()))==created,'created-record-unchanged')
            require(idle(),'playback-changed-do-not-delete');consumed['remove']=True
            request=urllib.request.Request(bridge.server_url+'/api/me/item/'+item+'/bookmark/'+str(choice),method='DELETE',
                headers={'Authorization':'Bearer '+bridge.api_key})
            with bridge.opener.open(request,timeout=10) as response:return response.status in (200,204)
        phase='one-bookmark-create-verify-remove'
        trial=BookmarkTrial(read,create,remove,ROOT/'writes',ACCOUNT,item,choice,title)
        result.update(trial.run())
        require(read()==before,'all-original-state-preserved')
        require(all(sha(Path('/storage')/p)==digest for p,digest in installed.items()),'installed-files-changed')
        result.update(installed_files_unchanged=True,account_verified=True,idle_empty=idle(),exact_one_create_and_delete=all(consumed.values()))
except Exception as error:
    result.update(passed=False,phase=phase,code=str(error) if isinstance(error,ProgressUnavailable) else 'one-bookmark-trial-failed',no_automatic_retry=True)
finally:
    output=BASE/('inspect-'+str(time.time_ns())+'.json') if mode=='inspect' or not ROOT.exists() else ROOT/('result-'+str(time.time_ns())+'.json')
    atomic(output,result);os.close(lock)
