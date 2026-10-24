"""HP-only read audit after discovering Kodi elides assert statements.

Run with system Python over approved SSH. No player, playlist, setting or
credential mutations. Existing-session secrets stay source-local/in memory.
"""
import hashlib,json,os,sys,time
from pathlib import Path

if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_jellyfin import PlaylistCreator
from music_playlists import server_id


def check_inventory(before,current):
    """Existing entries are immutable; separately count, never adopt/delete additions."""
    old={row['Id']:row for row in before};new={row['Id']:row for row in current}
    if len(old)!=len(before) or len(new)!=len(current):raise RuntimeError('duplicate-playlist-identity')
    if any(identity not in new or new[identity]!=row for identity,row in old.items()):
        raise RuntimeError('original-playlist-content-or-access-drift')
    return len(new.keys()-old.keys())

root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
creator=PlaylistCreator('/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/data.json')
listing=creator.list_playlists()
if len(listing.get('Items',[]))!=listing.get('TotalRecordCount'):raise RuntimeError('truncated-inventory')
current=sorted([dict(Id=row['Id'],Name=row['Name'],Type=row['Type'],MediaType=row.get('MediaType'),
    details=creator.playlist_details(row['Id'])) for row in listing['Items']],key=lambda row:row['Id'])
ui=root/'shared-save-ui-1792860791946956675'
trial=root/'shared-save-1792859893121517673'
before=json.loads((ui/'existing-before.json').read_text())
if len(before)!=16:raise RuntimeError('unexpected-original-inventory')
additional=check_inventory(before,current)
for path in (ui/'existing-after.json',trial/'existing-playlists-before.json',trial/'existing-playlists-after.json'):
    prior=json.loads(path.read_text())
    # Earlier raw IDs may include GUID hyphens; compare canonical identities.
    normalized=lambda rows:[dict(row,Id=server_id(row['Id'])) for row in rows]
    if sorted(normalized(prior),key=lambda r:r['Id'])!=sorted(normalized(before),key=lambda r:r['Id']):
        raise RuntimeError('saved-inventory-evidence-disagrees')
ui_saved=json.loads((ui/'verified-new-playlist.json').read_text())
details=ui_saved['details'];record=ui_saved['record']
ids=details.get('ItemIds')
if (record.get('status')!='verified' or details.get('OpenAccess') is not False
        or not isinstance(ids,list) or len(ids)!=record['count'] or len(ids)!=5):
    raise RuntimeError('saved-ui-private-order-evidence-invalid')
if any(server_id(row.get('UserId'))!=creator.user_id for row in details.get('Shares',[])):
    raise RuntimeError('saved-ui-shared-to-another-user')
trial_saved=json.loads((trial/'created-playlist.json').read_text())
proof=json.loads((trial/'verified-before-delete.json').read_text())
if proof.get('verified') is not True or trial_saved['details'].get('OpenAccess') is not False:
    raise RuntimeError('saved-programmatic-private-evidence-invalid')
existing={server_id(row['Id']) for row in current}
if server_id(record['playlist_id']) in existing or server_id(trial_saved['Id']) in existing:
    raise RuntimeError('disposable-playlist-still-present')
result=dict(original_playlists_verified=16,original_order_and_access_unchanged=True,
    current_playlist_count=len(current),additional_playlists_preserved=additional,
    disposable_playlists_absent=True,saved_ui_private_five_occurrences=True,
    saved_programmatic_explicit_verifier_passed=True,no_server_writes=True,
    no_playback_writes=True,canonical_identity_verified=True,
    inventory_sha256=hashlib.sha256(json.dumps(current,sort_keys=True).encode()).hexdigest())
path=root/('readonly-audit-'+str(time.time_ns())+'.json')
with path.open('x') as output:json.dump(result,output,sort_keys=True)
path.chmod(0o600)
print(json.dumps(dict(evidence=path.name,**result)))
