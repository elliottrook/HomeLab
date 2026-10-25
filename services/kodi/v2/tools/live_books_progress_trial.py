"""One approved HP book + podcast create/resume trial; never normal sync activation."""
import fcntl,hashlib,importlib.util,json,os,shutil,sys,time,urllib.request
from pathlib import Path
import xbmc,xbmcgui
sys.path.insert(0,str(Path(__file__).resolve().parent))
from books_progress import Scope,Draft,require,identifier,timeline,resume_target,ProgressUnavailable
from books_progress_reader import Reader
from books_progress_trial import TrialWriter
STORAGE=Path('/storage');CHECK=STORAGE/'.aster-checkpoints/aster-books-progress-20261025/trial1'
ACCOUNT='5326816b7ef0f98b2ab17a43d8502a3763947d1bad27f8bd10f6e2ac85bcc206'
BRIDGE='f37d51aec0bb8b48c1d31e9f9c442e4476130630b67a5bdc070af18dfd1a5c67'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Playlist.Clear'),'trial-rpc-boundary')
    if method=='Playlist.Clear':require(params=={'playlistid':0},'trial-audio-queue-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'trial-native-request-failed');return reply['result']
def queue(index):return rpc('Playlist.GetItems',dict(playlistid=index,properties=['file'],limits=dict(start=0,end=2)))
def idle():return not rpc('Player.GetActivePlayers') and all(queue(i)['limits']['total']==0 for i in (0,1))
def until(check,code,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise ProgressUnavailable(code)

require(os.uname().nodename=='AsterTV','hp-only')
require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-required')
require(not CHECK.exists(),'trial-already-started-no-repeat')
lock=os.open(STORAGE/'.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
CHECK.mkdir(mode=0o700,parents=True)
result=dict(passed=False,shared_household_position=True,normal_ui_connected=False,production_changed=False,checks=[])
player=xbmc.Player();owned_url=None;stop_requested=False;phase='preflight'
def owns():
    try:return owned_url is not None and player.isPlayingAudio() and player.getPlayingFile()==owned_url
    except Exception:return False
def stop_owned():
    global stop_requested
    require(owns() and not stop_requested,'trial-stop-ownership-required')
    stop_requested=True;player.stop()
    until(lambda:not rpc('Player.GetActivePlayers'),'trial-stop-not-confirmed',5)
    video=queue(1);require(video['limits']['total']==0,'foreign-video-queue')
    before=queue(0)
    if before['limits']['total']:
        require(before['limits']['total']==1 and len(before.get('items',[]))==1
            and before['items'][0].get('file')==owned_url,'trial-queue-not-owned')
        require(queue(0)==before and not rpc('Player.GetActivePlayers'),'trial-queue-changed')
        rpc('Playlist.Clear',dict(playlistid=0))
    require(idle(),'trial-queue-not-restored')
def play(url,position=None):
    global owned_url,stop_requested
    require(idle(),'idle-before-each-play')
    owned_url=url;stop_requested=False
    item=xbmcgui.ListItem(label='Aster HP shared-progress trial',path=url)
    item.setInfo('music',dict(title='Aster HP shared-progress trial'))
    player.play(url,item)
    until(owns,'trial-audio-start-not-confirmed')
    if position is not None:
        player.seekTime(position)
        until(lambda:owns() and position-1<=player.getTime()<=position+4,'trial-resume-seek-not-confirmed',8)
    else:until(lambda:owns() and player.getTime()>=8,'trial-clock-not-advancing',15)

try:
    bridge_path=STORAGE/'.kodi/addons/plugin.audio.asterbooks/resources/lib/bridge.py'
    require(sha(bridge_path)==BRIDGE,'approved-bridge-required')
    spec=importlib.util.spec_from_file_location('existing_audio_bridge',bridge_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    files=['plugin.audio.asterbooks/resources/lib/bridge.py','plugin.audio.asterbooks/service.py',
        'plugin.audio.asterbooks/default.py','skin.asterhome/tools/books_player.py','skin.asterhome/1080i/MyMusicNav.xml']
    before={}
    for name in files:
        source=STORAGE/'.kodi/addons'/name;require(not source.is_symlink(),'checkpoint-source-linked')
        target=CHECK/'before'/name;target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        shutil.copyfile(source,target);target.chmod(0o600)
        before[name]=sha(source);require(sha(target)==before[name],'checkpoint-failed')
    (CHECK/'before-files.json').write_text(json.dumps(before,indent=2));(CHECK/'before-files.json').chmod(0o600)
    profile=STORAGE/'.kodi/userdata/addon_data/plugin.audio.asterbooks'
    origin,key=module.load_config(profile/'client.json');bridge=module.Bridge(origin,key);del key
    reader=Reader(bridge.upstream);account=reader.account()
    require(account.limited and account.fingerprint==ACCOUNT,'approved-household-account-required')
    feed=STORAGE/'.kodi/userdata/addon_data/skin.asterhome/feeds/books.json'
    require(feed.stat().st_size<4*1024*1024,'bounded-catalogue-required')
    records=json.loads(feed.read_text())['items'];require(isinstance(records,list) and len(records)<=2000,'bounded-catalogue-required')
    selections=[]
    for kind in ('audiobook','podcast'):
        record=next(r for r in records if r.get('authority')=='audiobookshelf' and r.get('media_type')==kind)
        item_id=identifier(record.get('authority_id'));metadata=bridge.metadata(item_id)
        require(metadata.get('id')==item_id and metadata.get('mediaType')==('book' if kind=='audiobook' else 'podcast'),'exact-metadata-required')
        media=metadata['media'];episode_id=None
        if kind=='audiobook':
            files=media['audioFiles'];require(len(files)==1,'single-file-book-trial-only')
            duration=files[0]['duration'];signature=[str(files[0]['ino'])]
        else:
            episodes=[e for e in media['episodes'] if isinstance(e.get('audioFile'),dict)
                and module.INO.fullmatch(str(e['audioFile'].get('ino')))]
            require(bool(episodes),'downloaded-episode-required')
            episode_id=identifier(episodes[0]['id']);duration=episodes[0]['audioFile']['duration']
            signature=[(e['id'],str(e['audioFile']['ino'])) for e in episodes]
        spans=timeline([duration]);scope=Scope(account.identity,kind,item_id,episode_id)
        require(reader.progress(account,kind,item_id,episode_id) is None,'initial-progress-must-be-absent')
        entries=module.control_request(profile/module.CONTROL_SOCKET,kind,item_id)
        require(bool(entries),'audio-capability-required')
        second=bridge.metadata(item_id)['media']
        now=[str(f['ino']) for f in second['audioFiles']] if kind=='audiobook' else [(e['id'],str(e['audioFile']['ino'])) for e in second['episodes']
            if isinstance(e.get('audioFile'),dict) and module.INO.fullmatch(str(e['audioFile'].get('ino')))]
        require(signature==now,'metadata-changing-no-play')
        from urllib.parse import urlsplit
        url=entries[0]['url'];parts=urlsplit(url)
        require(parts.scheme=='http' and parts.hostname=='127.0.0.1' and parts.port
            and module.CAP.fullmatch(parts.path) and not parts.query and not parts.fragment,'private-audio-capability-required')
        selections.append((scope,spans,url))
    allowed=frozenset(s for s,_,_ in selections)
    def patch(scope,payload):
        require(scope in allowed and not payload['isFinished'],'approved-create-only-position')
        path='/api/me/progress/'+scope.item+('/'+scope.episode if scope.episode else '')
        request=urllib.request.Request(bridge.server_url+path,data=json.dumps(payload).encode(),method='PATCH',
            headers={'Authorization':'Bearer '+bridge.api_key,'Content-Type':'application/json'})
        with bridge.opener.open(request,timeout=15) as response:return response.status==200
    writer=TrialWriter(reader,patch,CHECK/'writes',allowed)
    (CHECK/'targets-private.json').write_text(json.dumps([dict(kind=s.kind,item=s.item,episode=s.episode) for s,_,_ in selections]))
    (CHECK/'targets-private.json').chmod(0o600)
    for scope,spans,url in selections:
        phase=scope.kind+'-play';play(url)
        require(owns() and abs(player.getTotalTime()-spans[0].duration)<=2,'trial-media-duration-mismatch')
        position=player.getTime();require(0<position<30,'bounded-trial-position')
        stop_owned();owned_url=None
        phase=scope.kind+'-save'
        saved=writer.save_new_once(Draft(scope,spans[0].duration,position,False))
        target=resume_target(saved,spans);require(target[0]==0,'single-file-resume-target')
        phase=scope.kind+'-resume';play(url,target[1]);xbmc.sleep(1000)
        require(owns() and target[1]-1<=player.getTime()<=target[1]+6,'saved-position-resume-failed')
        stop_owned();owned_url=None
        result['checks'].append(dict(kind=scope.kind,saved_new_position=True,server_readback_verified=True,
            resume_seek_verified=True,stop_and_queue_cleanup=True))
    require(all(sha(STORAGE/'.kodi/addons'/name)==digest for name,digest in before.items()),'installed-files-changed')
    require(idle(),'final-idle-required')
    result.update(passed=True,server_positions_created=2,installed_files_unchanged=True,account_sha256=account.fingerprint)
except Exception:
    result.update(code='bounded-books-progress-trial-failed',phase=phase,no_automatic_retry=True)
finally:
    if owns() and not stop_requested:
        try:stop_owned()
        except Exception:result['cleanup_uncertain']=True
    result['idle_empty']=idle()
    path=CHECK/'trial-result.json'
    with path.open('x') as handle:json.dump(result,handle,indent=2)
    path.chmod(0o600);os.close(lock)
