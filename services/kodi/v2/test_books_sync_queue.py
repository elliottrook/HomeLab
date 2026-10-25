import copy,json,tempfile,unittest
from pathlib import Path
from books_progress import Scope,timeline,ProgressUnavailable
from books_sync import Registry,Binding,QueueCleaner
class QueueTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.scope=Scope('tv','audiobook','book');self.registry=Registry(clock=lambda:0)
        for url in ('one','two'):self.registry.add(url,Binding(self.scope,timeline([100]),0,0,False,100))
        self.players=[];self.video=[];self.audio=[dict(file='one'),dict(file='two')];self.calls=[];self.failure=False
        self.cleaner=QueueCleaner(self.registry,self.rpc,Path(temp.name)/'journal')
    def rpc(self,method,params):
        self.calls.append((method,params))
        if method=='Player.GetActivePlayers':return self.players
        if method=='Playlist.GetItems':
            items=self.audio if params['playlistid']==0 else self.video
            return dict(limits=dict(start=0,end=len(items),total=len(items)),items=copy.deepcopy(items))
        if method=='Playlist.Clear':
            self.audio=[]
            if self.failure:raise TimeoutError('private-path')
            return 'OK'
        raise RuntimeError('unexpected')
    def test_owned_queue_only_and_verified(self):
        self.assertTrue(self.cleaner.clean(self.scope));self.assertEqual(self.audio,[])
        self.assertEqual(sum(m=='Playlist.Clear' for m,p in self.calls),1)
        self.assertEqual(json.loads(self.cleaner.path.read_text())['status'],'verified')
        self.cleaner.clean(self.scope);self.assertEqual(sum(m=='Playlist.Clear' for m,p in self.calls),1)
    def test_active_foreign_or_video_queue_untouched(self):
        for mode in ('player','audio','video'):
            self.players=[dict(playerid=0)] if mode=='player' else []
            self.audio=[dict(file='foreign')] if mode=='audio' else [dict(file='one')]
            self.video=[dict(file='foreign')] if mode=='video' else []
            self.assertFalse(self.cleaner.clean(self.scope))
        self.assertFalse(any(m=='Playlist.Clear' for m,p in self.calls))
    def test_unknown_result_fenced_across_restart_no_retry(self):
        self.failure=True
        with self.assertRaisesRegex(ProgressUnavailable,'uncertain'):self.cleaner.clean(self.scope)
        newer=QueueCleaner(self.registry,self.rpc,self.cleaner.path.parent)
        with self.assertRaisesRegex(ProgressUnavailable,'review'):newer.clean(self.scope)
        self.assertEqual(sum(m=='Playlist.Clear' for m,p in self.calls),1)
    def test_related_podcast_episode_queue_allowed_but_other_show_refused(self):
        scope=Scope('tv','podcast','show','first')
        self.registry.add('pod1',Binding(scope,timeline([100]),0,0,True,100))
        self.registry.add('pod2',Binding(Scope('tv','podcast','show','second'),timeline([100]),0,0,True,100))
        self.audio=[dict(file='pod1'),dict(file='pod2')];self.assertTrue(self.cleaner.clean(scope))
        self.audio=[dict(file='one')];self.assertFalse(self.cleaner.clean(scope))
