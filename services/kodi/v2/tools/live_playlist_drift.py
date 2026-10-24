"""HP read-only playlist drift summary. Never print names, IDs, URLs or tokens."""
import json,os,sys
from collections import Counter
from pathlib import Path

if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_jellyfin import PlaylistCreator

reader=PlaylistCreator('/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/data.json')
response=reader.list_playlists()
if len(response.get('Items',[]))!=response.get('TotalRecordCount'):raise RuntimeError('truncated-inventory')
current={row['Id']:dict(Id=row['Id'],Name=row['Name'],Type=row['Type'],MediaType=row.get('MediaType'),
    details=reader.playlist_details(row['Id'])) for row in response['Items']}
path=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024/shared-save-ui-1792860791946956675/existing-before.json')
before={row['Id']:row for row in json.loads(path.read_text())}
top=Counter();details=Counter();changed=0;item_counts=[]
for identity in before.keys()&current.keys():
    a,b=before[identity],current[identity]
    if a==b:continue
    changed+=1
    for key in ('Name','Type','MediaType'):
        if a.get(key)!=b.get(key):top[key]+=1
    for key in a['details'].keys()|b['details'].keys():
        if a['details'].get(key)!=b['details'].get(key):
            safe=key if key in ('ItemIds','OpenAccess','Shares','UserId','Id','Name') else 'other-field'
            details[safe]+=1
    old=a['details'].get('ItemIds',[]);new=b['details'].get('ItemIds',[])
    if old!=new:item_counts.append(dict(before=len(old),current=len(new),added=len(set(new)-set(old)),removed=len(set(old)-set(new)),same_members=set(old)==set(new)))
root=path.parent
ui=json.loads((root/'verified-new-playlist.json').read_text())
trial=json.loads((root.parent/'shared-save-1792859893121517673/created-playlist.json').read_text())
additional=set(current)-set(before)
ui_id=ui['record']['playlist_id'];trial_id=trial['Id']
from music_playlists import server_id
additional={server_id(value):current[value] for value in additional}
ui_returned=server_id(ui_id) in additional
print(json.dumps(dict(before_count=len(before),current_count=len(current),same_playlist_identities=set(before)==set(current),
    changed_playlists=changed,changed_top_fields=dict(top),changed_detail_fields=dict(details),item_changes=item_counts,
    previous_ui_trial_returned=ui_returned,previous_programmatic_trial_returned=server_id(trial_id) in additional,
    returned_ui_details_unchanged=ui_returned and additional[server_id(ui_id)]['details']==ui['details'],no_server_writes=True)))
