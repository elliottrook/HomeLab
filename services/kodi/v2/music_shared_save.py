"""Owned-queue create-only shared save with a persistent uncertain-write gate."""
import json,time
from pathlib import Path
from music_playlist_save import PlaylistSaveUnavailable,plan_save,create_once,verify_created,write_journal
from music_playlists import read_playlists


def save_owned_queue(engine,expected,name,creator,mapping,profile,*,confirmed=False,cancelled=lambda:False):
    if confirmed is not True:raise PlaylistSaveUnavailable('playlist-save-confirmation-required')
    profile=Path(profile);pending=profile/'shared-playlist-pending.json'
    if pending.exists():
        try:previous=json.loads(pending.read_text())
        except Exception:raise PlaylistSaveUnavailable('shared-save-recovery-required') from None
        if not isinstance(previous,dict) or previous.get('status') not in ('verified','cancelled-before-request'):
            raise PlaylistSaveUnavailable('shared-save-recovery-required')
    with engine.lock:
        engine.check_cancel()
        state=engine.observe()
        if state.fingerprint!=expected:raise PlaylistSaveUnavailable('queue-preview-stale')
        rows=read_playlists(creator,include_other=True)
        plan=plan_save(state,name,mapping(state.song_ids),creator.user_id,
                       [dict(Id=r['playlistid'],Name=r['label']) for r in rows])
        engine.check_cancel()
        if cancelled():raise PlaylistSaveUnavailable('playlist-save-cancelled')
        current=engine.observe()
        if current.fingerprint!=expected:raise PlaylistSaveUnavailable('queue-preview-stale')
        def journal(record):write_journal(pending,{**record,'queue_fingerprint':expected})
        request_started=[False]
        def post(method,path,body):
            engine.check_cancel()
            if cancelled():raise PlaylistSaveUnavailable('playlist-save-cancelled')
            request_started[0]=True
            return creator(method,path,body)
        try:identity=create_once(post,plan,current,confirmed=True,journal=journal)
        except PlaylistSaveUnavailable:
            if not request_started[0]:
                journal(dict(status='cancelled-before-request',name=plan.name))
                raise PlaylistSaveUnavailable('playlist-save-cancelled') from None
            raise
        # Once POST may have been sent, resolve its result even if Back arrives.
        # Never abandon it, retry it or auto-delete a playlist to hide failure.
        verify_created(plan,identity,creator.playlist_metadata(identity),creator.playlist_details(identity))
        record=dict(status='verified',playlist_id=identity,name=plan.name,count=len(plan.item_ids),queue_fingerprint=expected)
        write_journal(profile/('shared-playlist-saved-'+str(time.time_ns())+'.json'),record)
        write_journal(pending,record)
        return record
