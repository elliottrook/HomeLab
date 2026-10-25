"""HP GET-only timeline survey; project only counts/types, never paths or keys."""
import importlib.util,json,os,time
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
source=Path('/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib/bridge.py')
spec=importlib.util.spec_from_file_location('audit_bridge',source)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
origin,key=module.load_config(Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks/client.json'))
bridge=module.Bridge(origin,key);del key
feed=json.loads(Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/books.json').read_text())
rows=[r for r in feed['items'] if r.get('authority')=='audiobookshelf' and r.get('media_type')=='audiobook']
result=dict(kind='hp-multifile-read.v1',read_only=True,examined=0,single=0,multiple=0,errors=0,samples=[])
private=[]
for row in rows[:80]:
    try:
        item=bridge.metadata(row['authority_id']);media=item['media'];files=media.get('audioFiles',[])
        result['examined']+=1
        if len(files)==1:result['single']+=1
        elif len(files)>1:
            result['multiple']+=1;tracks=media.get('tracks',[])
            result['samples'].append(dict(files=len(files),tracks=len(tracks),
                file_fields=sorted(files[0]),track_fields=sorted(tracks[0]) if tracks else [],
                indices=[f.get('index') for f in files[:10]],
                track_indices=[t.get('index') for t in tracks[:10]],
                track_inode_match=len(files)==len(tracks) and all(str(f.get('ino'))==str(t.get('ino')) for f,t in zip(files,tracks))))
            private.append(dict(item=item['id'],media=media))
            if len(private)>=3:break
    except Exception:result['errors']+=1
root=Path('/storage/.aster-checkpoints/aster-books-sync-20261025');stamp=str(time.time_ns())
for name,value in (('multifile-audit-',result),('multifile-private-',private)):
    path=root/(name+stamp+'.json')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream)
print(json.dumps(result))
