import threading
import unittest

from music_expanded_trial import ExpandedTrial
from music_progressive import ProgressiveSession
from music_trial import TrialUnavailable
from test_music_trial import FakePlayer


class ProgressiveTests(unittest.TestCase):
    def make(self,n=430,**kwargs):
        self.player=FakePlayer();self.journal=[]
        self.engine=ExpandedTrial(self.player,list(range(1,n+1)),lambda s:True,
            queue_limit=20000,sleep=lambda n:None,
            intent=lambda s,**kw:self.journal.append((s,kw)))
        self.session=ProgressiveSession(self.engine,**kwargs)
        return self.session

    def test_starts_small_then_fills_exact_order_without_reopen(self):
        session=self.make(fill_batch=200);session.start(list(range(1,431)),confirmed=True)
        session.worker.join()
        self.assertEqual(session.status()['phase'],'ready')
        self.assertEqual(self.player.ids,list(range(1,431)))
        self.assertEqual(sum(m=='Player.Open' for m,p in self.player.calls),1)
        adds=[len(p['item']) for m,p in self.player.calls if m=='Playlist.Add']
        self.assertEqual(adds,[25,200,200,5])
        self.assertEqual(self.journal[-1][0].song_ids,tuple(range(1,431)))
        session.close();session.close();self.assertEqual(self.player.ids,[])

    def test_exit_waits_for_pending_batch_then_stops_and_never_readds(self):
        entered=threading.Event();release=threading.Event()
        session=self.make();original=self.engine.rpc;adds=0
        def rpc(method,p):
            nonlocal adds
            if method=='Playlist.Add':
                adds+=1
                if adds==2:entered.set();release.wait(2)
            return original(method,p)
        self.engine.rpc=rpc
        session.start(list(range(1,431)),confirmed=True)
        self.assertTrue(entered.wait(2))
        closer=threading.Thread(target=session.close);closer.start()
        self.assertTrue(closer.is_alive());release.set();closer.join(2)
        self.assertFalse(closer.is_alive());self.assertFalse(session.worker.is_alive())
        self.assertEqual(self.player.ids,[]);self.assertIsNone(self.player.position)
        self.assertEqual(adds,2)

    def test_external_queue_is_preserved_on_failure_and_close(self):
        session=self.make()
        self.engine.progress=lambda d,t:setattr(self.player,'ids',[99999]) if d==50 else None
        session.start(list(range(1,431)),confirmed=True);session.worker.join()
        self.assertEqual(session.status()['phase'],'failed')
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):session.close()
        self.assertEqual(self.player.ids,[99999])

    def test_requires_confirmation_and_no_repeat_start(self):
        session=self.make()
        with self.assertRaises(TrialUnavailable):session.start([1])
        self.assertFalse(any(m=='Playlist.Add' for m,p in self.player.calls))
        session.start([1],confirmed=True);session.worker.join()
        with self.assertRaises(TrialUnavailable):session.start([1],confirmed=True)
        session.close()

    def test_resource_failure_stops_loading_and_leaves_owned_cleanup_possible(self):
        calls=0
        def resources():
            nonlocal calls
            calls+=1
            if calls>1:raise TrialUnavailable('low-memory-stop')
        session=self.make(resource_check=resources)
        session.start(list(range(1,431)),confirmed=True);session.worker.join()
        self.assertEqual(session.status()['error'],'low-memory-stop')
        session.close();self.assertEqual(self.player.ids,[])

    def test_select_loaded_track_preserves_queue_and_validates_position(self):
        session=self.make();session.start(list(range(1,431)),confirmed=True);session.worker.join()
        before=list(self.player.ids);session.select(12)
        self.assertEqual(self.player.position,12);self.assertEqual(self.player.ids,before)
        for invalid in (True,-1,430):
            with self.assertRaises(TrialUnavailable):session.select(invalid)
        session.close()

    def test_pending_pause_takes_priority_over_another_fill_batch(self):
        session=self.make();entered=threading.Event();release=threading.Event()
        original=self.engine.rpc;adds=0
        def rpc(method,p):
            nonlocal adds
            if method=='Playlist.Add':
                adds+=1
                if adds==2:entered.set();release.wait(2)
            return original(method,p)
        self.engine.rpc=rpc;session.start(list(range(1,431)),confirmed=True)
        self.assertTrue(entered.wait(2))
        pause=threading.Thread(target=lambda:session.pause(False));pause.start()
        self.assertTrue(session.control_pending.wait(2));release.set();pause.join(2);session.worker.join(2)
        self.assertFalse(pause.is_alive());self.assertFalse(session.worker.is_alive())
        methods=[m for m,p in self.player.calls]
        add_positions=[i for i,m in enumerate(methods) if m=='Playlist.Add']
        self.assertLess(methods.index('Player.PlayPause'),add_positions[2])
        session.close()

    def test_natural_track_boundary_retries_only_snapshot_reads(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        original=self.engine.rpc;count=0
        def rpc(method,p):
            nonlocal count
            result=original(method,p)
            if method=='Player.GetProperties' and p['properties']==['playlistid','position']:
                count+=1
                if count==1:self.player.position=1
            return result
        self.engine.rpc=rpc;begin=len(self.player.calls)
        self.assertEqual(self.engine.observe().current_index,1)
        self.assertFalse(any(m in ('Player.Open','Playlist.Add','Playlist.Clear') for m,p in self.player.calls[begin:]))
        session.close()

    def test_metadata_lag_is_reread_without_accepting_unknown_playback(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        original=self.engine.rpc;count=0
        def rpc(method,p):
            nonlocal count
            if method=='Player.GetItem':
                count+=1
                if count==1:return {'item':{'type':'song'}}
            return original(method,p)
        self.engine.rpc=rpc
        self.assertEqual(self.engine.observe().current_index,0)
        self.assertEqual(count,2)
        def foreign(method,p):
            if method=='Player.GetItem':return {'item':{'type':'song','id':99999}}
            return original(method,p)
        self.engine.rpc=foreign
        with self.assertRaisesRegex(TrialUnavailable,'unrelated-playback'):self.engine.observe()
        self.engine.rpc=original;session.close()


if __name__=='__main__':unittest.main()
