"""Read at most one real book and podcast episode; no progress/session writes."""
import importlib.util,json,os,sys,time
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from books_progress_reader import Reader
from books_progress import Scope,timeline,resume_target,require,identifier
result=dict(kind='aster-books-progress-samples-read.v1',read_only=True,samples=[])
try:
    path=Path('/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib/bridge.py')
    spec=importlib.util.spec_from_file_location('existing_audio_bridge',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    origin,key=module.load_config(Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks/client.json'))
    bridge=module.Bridge(origin,key);del key
    reader=Reader(bridge.upstream);account=reader.account()
    require(account.limited,'limited-progress-account-required')
    feed=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/books.json')
    require(feed.stat().st_size<4*1024*1024,'bounded-local-feed-required')
    items=json.loads(feed.read_text())['items'];require(isinstance(items,list) and len(items)<=2000,'bounded-local-feed-required')
    for kind in ('audiobook','podcast'):
        record=next((r for r in items if isinstance(r,dict) and r.get('authority')=='audiobookshelf' and r.get('media_type')==kind),None)
        require(record is not None,'sample-kind-not-present');item=identifier(record.get('authority_id'))
        metadata=bridge.metadata(item)
        require(metadata.get('id')==item and metadata.get('mediaType')==('book' if kind=='audiobook' else 'podcast'),'sample-identity-mismatch')
        media=metadata['media'];require(isinstance(media,dict),'sample-metadata-required')
        episode=None;durations=[];mapping_ready=False
        if kind=='podcast':
            episodes=media.get('episodes',[]);require(isinstance(episodes,list) and len(episodes)<=1000,'bounded-episodes-required')
            entry=next((r for r in episodes if isinstance(r,dict) and isinstance(r.get('audioFile'),dict)),None)
            require(entry is not None,'downloaded-episode-required');episode=identifier(entry.get('id'))
            durations=[entry['audioFile'].get('duration')];mapping_ready=True
        else:
            files=media.get('audioFiles',[]);require(isinstance(files,list) and 0<len(files)<=1000,'bounded-audio-files-required')
            durations=[f.get('duration') for f in files]
            mapping_ready=len(files)==1
            # Multi-file order must be independently verified before any resume.
        progress=reader.progress(account,kind,item,episode)
        spans=timeline(durations);mapped=False
        if progress is not None and not progress.finished and mapping_ready:
            resume_target(progress,spans);mapped=True
        result['samples'].append(dict(kind=kind,progress_present=progress is not None,
            finished=progress.finished if progress else False,file_count=len(spans),
            stable_episode_identity=kind=='podcast',timeline_order_verified=mapping_ready,resume_mapped=mapped))
    require(reader.account()==account,'account-changed')
    result.update(passed=True,account_sha256=account.fingerprint,server_progress_writes=0)
except Exception:
    result.update(passed=False,code='books-progress-sample-audit-unavailable')
directory=Path('/storage/.aster-checkpoints/aster-books-progress-20261025');directory.mkdir(mode=0o700,parents=True,exist_ok=True)
path=directory/('samples-read-'+str(time.time_ns())+'.json')
with path.open('x') as f:json.dump(result,f,indent=2)
path.chmod(0o600);print(json.dumps(result))
