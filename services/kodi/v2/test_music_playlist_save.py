import unittest
from music_queue import QueueSnapshot
from music_playlist_save import PlaylistSaveUnavailable,create_once,plan_save,verify_created

USER='a'*32;ONE='1'*32;TWO='2'*32;NEW='3'*32;OLD='4'*32


class SharedSaveTests(unittest.TestCase):
    def setUp(self):
        self.queue=QueueSnapshot((1,2,1),0)
        self.plan=plan_save(self.queue,'Aster test',{1:ONE,2:TWO},USER,[dict(Id=OLD,Name='Existing')])
    def test_exact_duplicate_order_and_private_current_user_payload(self):
        self.assertEqual(self.plan.payload(),dict(Name='Aster test',UserId=USER,Ids=[ONE,TWO,ONE],MediaType='Audio',IsPublic=False))
    def test_no_overwrite_fuzzy_match_missing_or_invalid_server_identity(self):
        for args in ((self.queue,'existing',{1:ONE,2:TWO},USER,[dict(Id=OLD,Name=' Existing ')]),
                     (self.queue,'Name',{1:ONE},USER,[]),
                     (self.queue,'Name',{1:'https://private',2:TWO},USER,[]),
                     (self.queue,'Name\n',{1:ONE,2:TWO},USER,[])):
            with self.assertRaises(PlaylistSaveUnavailable):plan_save(*args)
    def test_create_is_one_post_with_durable_intent_before_mutation(self):
        events=[]
        def api(method,path,body):
            self.assertEqual(events[-1]['status'],'create-requested')
            events.append((method,path,body));return dict(Id=NEW)
        self.assertEqual(create_once(api,self.plan,self.queue,confirmed=True,journal=events.append),NEW)
        self.assertEqual([e[:2] for e in events if isinstance(e,tuple)],[('POST','/Playlists')])
        self.assertEqual(events[-1]['status'],'created-unverified')
    def test_stale_or_unconfirmed_never_calls_server(self):
        calls=[]
        for current,confirmed in ((self.queue,False),(self.queue,1),(QueueSnapshot((2,1),0),True)):
            with self.assertRaises(PlaylistSaveUnavailable):
                create_once(lambda *args:calls.append(args),self.plan,current,confirmed=confirmed,journal=lambda x:None)
        self.assertFalse(calls)
    def test_uncertain_post_is_not_retried_and_never_deletes(self):
        calls=[]
        def api(*args):calls.append(args);raise TimeoutError('private URL')
        with self.assertRaisesRegex(PlaylistSaveUnavailable,'^playlist-create-uncertain$'):
            create_once(api,self.plan,self.queue,confirmed=True,journal=lambda x:None)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],'POST')
    def test_existing_id_response_is_never_accepted_for_cleanup(self):
        with self.assertRaisesRegex(PlaylistSaveUnavailable,'identity-collision'):
            create_once(lambda *args:dict(Id=OLD),self.plan,self.queue,confirmed=True,journal=lambda x:None)
    def test_verification_requires_exact_order_private_audio_and_only_current_user_shares(self):
        metadata=dict(Id=NEW,Name='Aster test',Type='Playlist',MediaType='Audio',OwnerId=USER)
        details=dict(OpenAccess=False,ItemIds=[ONE,TWO,ONE],Shares=[])
        self.assertTrue(verify_created(self.plan,NEW,metadata,details))
        for change in (dict(OpenAccess=True),dict(ItemIds=[ONE,TWO]),dict(Shares=[dict(UserId=OLD)])):
            with self.assertRaises(PlaylistSaveUnavailable):verify_created(self.plan,NEW,metadata,{**details,**change})
        with self.assertRaises(PlaylistSaveUnavailable):verify_created(self.plan,NEW,{**metadata,'OwnerId':OLD},details)
