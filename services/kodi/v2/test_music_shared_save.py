import json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import Mock
from music_queue import QueueSnapshot
from music_shared_save import save_owned_queue
from music_playlist_save import PlaylistSaveUnavailable,write_journal
from music_jellyfin import PlaylistCreator

USER='a'*32;ONE='1'*32;TWO='2'*32;NEW='3'*32


class Creator:
    user_id=USER
    def __init__(self):self.calls=[];self.body=None
    def list_playlists(self):return dict(Items=[],TotalRecordCount=0)
    def __call__(self,method,path,body):self.calls.append((method,path));self.body=body;return dict(Id=NEW)
    def playlist_metadata(self,identity):return dict(Id=identity,Name=self.body['Name'],Type='Playlist',MediaType='Audio',OwnerId=USER)
    def playlist_details(self,identity):return dict(ItemIds=self.body['Ids'],OpenAccess=False,Shares=[])


class SharedSaveTests(unittest.TestCase):
    def setUp(self):
        self.queue=QueueSnapshot((1,2,1),0)
        self.engine=Mock();self.engine.lock=threading.RLock();self.engine.observe.return_value=self.queue
        self.creator=Creator()
    def save(self,path,**kw):
        return save_owned_queue(self.engine,self.queue.fingerprint,'Saved',self.creator,lambda ids:{1:ONE,2:TWO},path,**kw)
    def test_confirmation_is_mandatory_before_any_read_or_write(self):
        with tempfile.TemporaryDirectory() as folder:
            for value in (False,1):
                with self.assertRaisesRegex(PlaylistSaveUnavailable,'confirmation'):self.save(folder,confirmed=value)
        self.engine.observe.assert_not_called();self.assertFalse(self.creator.calls)
    def test_verified_save_has_private_journal_exact_order_and_no_player_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            result=self.save(folder,confirmed=True)
            self.assertEqual(self.creator.calls,[('POST','/Playlists')])
            self.assertEqual(self.creator.body['Ids'],[ONE,TWO,ONE])
            pending=Path(folder)/'shared-playlist-pending.json'
            self.assertEqual(json.loads(pending.read_text()),result)
            self.assertEqual(pending.stat().st_mode&0o777,0o600)
            self.assertEqual(len(list(Path(folder).glob('shared-playlist-saved-*.json'))),1)
        self.engine.write.assert_not_called()
    def test_uncertain_request_is_sticky_and_never_repeated_after_restart(self):
        class Uncertain(Creator):
            def __call__(self,*args):self.calls.append(args);raise TimeoutError('secret')
        self.creator=Uncertain()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'uncertain'):self.save(folder,confirmed=True)
            self.assertEqual(len(self.creator.calls),1)
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'recovery-required'):self.save(folder,confirmed=True)
            self.assertEqual(len(self.creator.calls),1)
    def test_corrupt_pending_blocks_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'shared-playlist-pending.json').write_text('broken')
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'recovery-required'):self.save(folder,confirmed=True)
        self.assertFalse(self.creator.calls)
    def test_cancel_before_post_and_stale_queue_do_not_create(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'cancelled'):self.save(folder,confirmed=True,cancelled=lambda:True)
            self.engine.observe.return_value=QueueSnapshot((2,1),0)
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'stale'):self.save(folder,confirmed=True)
        self.assertFalse(self.creator.calls)
    def test_cancel_at_final_send_gate_is_known_unsent_not_sticky_uncertainty(self):
        checks=[]
        def cancelled():checks.append(True);return len(checks)>1
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'cancelled'):self.save(folder,confirmed=True,cancelled=cancelled)
            self.assertEqual(json.loads((Path(folder)/'shared-playlist-pending.json').read_text())['status'],'cancelled-before-request')
            self.save(folder,confirmed=True)
        self.assertEqual(self.creator.calls,[('POST','/Playlists')])
    def test_created_but_wrong_order_keeps_unverified_recovery_gate(self):
        self.creator.playlist_details=lambda identity:dict(ItemIds=[ONE],OpenAccess=False,Shares=[])
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'verification'):self.save(folder,confirmed=True)
            self.assertEqual(json.loads((Path(folder)/'shared-playlist-pending.json').read_text())['status'],'created-unverified')
            with self.assertRaisesRegex(PlaylistSaveUnavailable,'recovery-required'):self.save(folder,confirmed=True)
        self.assertEqual(self.creator.calls,[('POST','/Playlists')])
    def test_creator_refuses_delete_update_foreign_owner_or_public_access_before_http(self):
        creator=object.__new__(PlaylistCreator);creator.user_id=USER;creator.opener=Mock()
        body=dict(Name='Saved',UserId=USER,Ids=[ONE],MediaType='Audio',IsPublic=False)
        for method,path,data in (('DELETE','/Items/'+NEW,None),('POST','/Playlists/'+NEW,body),
                                 ('POST','/Playlists',{**body,'UserId':ONE}),('POST','/Playlists',{**body,'IsPublic':True})):
            with self.assertRaises(PlaylistSaveUnavailable):creator(method,path,data)
        creator.opener.open.assert_not_called()
