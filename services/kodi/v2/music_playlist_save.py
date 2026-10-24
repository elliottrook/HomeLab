"""Create-only shared-playlist plans: exact IDs/order, no credential access."""
from dataclasses import dataclass
import re
import json,os,tempfile
from pathlib import Path
from music_queue import QueueSnapshot


class PlaylistSaveUnavailable(ValueError):
    pass


def uuid(value):
    if not isinstance(value,str):raise PlaylistSaveUnavailable('invalid-server-identity')
    if not (re.fullmatch(r'[0-9a-fA-F]{32}',value) or re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',value)):
        raise PlaylistSaveUnavailable('invalid-server-identity')
    return value.replace('-','').lower()


@dataclass(frozen=True)
class SharedPlaylistPlan:
    name:str
    user_id:str
    item_ids:tuple
    queue_fingerprint:str
    existing_ids:frozenset

    def payload(self):
        return dict(Name=self.name,UserId=self.user_id,Ids=list(self.item_ids),MediaType='Audio',IsPublic=False)


def plan_save(snapshot,name,mapping,user_id,existing):
    if not isinstance(snapshot,QueueSnapshot) or not 1<=len(snapshot.song_ids)<=20000:
        raise PlaylistSaveUnavailable('nonempty-owned-queue-required')
    if (not isinstance(name,str) or not 1<=len(name.strip())<=100
            or any(ord(c)<32 or ord(c)==127 for c in name)):
        raise PlaylistSaveUnavailable('invalid-playlist-name')
    if not isinstance(mapping,dict) or not isinstance(existing,list):
        raise PlaylistSaveUnavailable('invalid-playlist-preview')
    ids=[]
    for song in snapshot.song_ids:
        if song not in mapping:raise PlaylistSaveUnavailable('song-not-mapped-to-server')
        ids.append(uuid(mapping[song]))
    existing_ids=set()
    for row in existing:
        if not isinstance(row,dict) or not isinstance(row.get('Name'),str):
            raise PlaylistSaveUnavailable('invalid-playlist-preview')
        identity=uuid(row.get('Id'))
        if identity in existing_ids:raise PlaylistSaveUnavailable('invalid-playlist-preview')
        existing_ids.add(identity)
        if row['Name'].strip().casefold()==name.strip().casefold():
            raise PlaylistSaveUnavailable('playlist-name-already-exists')
    return SharedPlaylistPlan(name.strip(),uuid(user_id),tuple(ids),snapshot.fingerprint,frozenset(existing_ids))


def create_once(api,plan,current,*,confirmed=False,journal):
    if type(confirmed) is not bool or not confirmed:
        raise PlaylistSaveUnavailable('playlist-save-confirmation-required')
    if not isinstance(plan,SharedPlaylistPlan) or not isinstance(current,QueueSnapshot) or current.fingerprint!=plan.queue_fingerprint:
        raise PlaylistSaveUnavailable('queue-preview-stale')
    journal(dict(status='create-requested',name=plan.name,user_id=plan.user_id,item_ids=plan.item_ids))
    try:response=api('POST','/Playlists',plan.payload())
    except Exception:
        # A timed-out POST may already have created a playlist. Never retry it,
        # overwrite by name, or delete anything based on an uncertain result.
        raise PlaylistSaveUnavailable('playlist-create-uncertain') from None
    try:identity=uuid(response.get('Id'))
    except (AttributeError,PlaylistSaveUnavailable):
        raise PlaylistSaveUnavailable('playlist-create-uncertain') from None
    if identity in plan.existing_ids:raise PlaylistSaveUnavailable('playlist-create-identity-collision')
    journal(dict(status='created-unverified',playlist_id=identity,name=plan.name,item_ids=plan.item_ids))
    return identity


def verify_created(plan,identity,metadata,details):
    identity=uuid(identity)
    if identity in plan.existing_ids:raise PlaylistSaveUnavailable('not-a-new-playlist')
    if (not isinstance(metadata,dict) or uuid(metadata.get('Id'))!=identity
            or metadata.get('Name')!=plan.name or metadata.get('Type')!='Playlist'
            or metadata.get('MediaType')!='Audio' or not isinstance(details,dict)
            or details.get('OpenAccess') is not False or not isinstance(details.get('ItemIds'),list)
            or tuple(uuid(i) for i in details['ItemIds'])!=plan.item_ids):
        raise PlaylistSaveUnavailable('playlist-verification-failed')
    if metadata.get('OwnerId') is not None and uuid(metadata['OwnerId'])!=plan.user_id:
        raise PlaylistSaveUnavailable('playlist-owner-mismatch')
    shares=details.get('Shares')
    if not isinstance(shares,list) or any(not isinstance(s,dict) or uuid(s.get('UserId'))!=plan.user_id for s in shares):
        raise PlaylistSaveUnavailable('unexpected-playlist-sharing')
    return True


def write_journal(path,record):
    path=Path(path);path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    data=json.dumps(record,sort_keys=True).encode()
    fd,name=tempfile.mkstemp(prefix='.playlist-save-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as output:
            output.write(data);output.flush();os.fsync(output.fileno())
        if Path(name).read_bytes()!=data:raise PlaylistSaveUnavailable('playlist-journal-verification-failed')
        os.replace(name,path)
    finally:
        if Path(name).exists():Path(name).unlink()
