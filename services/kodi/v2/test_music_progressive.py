import threading
import unittest

from music_expanded_trial import ExpandedTrial
from music_progressive import ProgressiveSession,clock_milliseconds,clock_label
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

    def test_clock_format_and_invalid_metadata_are_truthful(self):
        self.assertEqual(clock_milliseconds(dict(hours=1,minutes=2,seconds=3,milliseconds=456)),3723456)
        self.assertEqual(clock_label(3723456),'1:02:03');self.assertEqual(clock_label(65000),'1:05')
        for value in (None,{},dict(hours=True,minutes=0,seconds=0,milliseconds=0),
                      dict(hours=0,minutes=60,seconds=0,milliseconds=0)):
            with self.assertRaises(TrialUnavailable):clock_milliseconds(value)

    def test_seek_is_small_owned_and_preserves_pause_and_queue(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        session.pause(False);before=list(self.player.ids)
        session.seek(10);self.assertEqual(self.player.elapsed,35000)
        session.seek(-10);self.assertEqual(self.player.elapsed,25000)
        self.assertEqual(self.player.speed,0);self.assertEqual(self.player.ids,before)
        self.player.elapsed=3000;session.seek(-10);self.assertEqual(self.player.elapsed,0)
        self.player.elapsed=178000;session.seek(10);self.assertEqual(self.player.elapsed,179000)
        calls=len(self.player.calls);session.seek(10)
        self.assertFalse(any(m=='Player.Seek' for m,p in self.player.calls[calls:]))
        session.close()

    def test_seek_refuses_unknown_duration_unsupported_external_and_closed(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        for offset in (True,1,100):
            with self.assertRaises(TrialUnavailable):session.seek(offset)
        self.player.canseek=False
        with self.assertRaisesRegex(TrialUnavailable,'seek-unavailable'):session.seek(10)
        self.player.canseek=True;self.player.duration=0
        with self.assertRaisesRegex(TrialUnavailable,'seek-unavailable'):session.seek(10)
        self.player.duration=180000;self.player.ids=[99999]
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):session.seek(10)
        self.assertFalse(any(m=='Player.Seek' for m,p in self.player.calls))
        self.player.ids=[1,2,3];session.close()
        with self.assertRaisesRegex(TrialUnavailable,'session-closed'):session.seek(10)

    def test_seek_rechecks_song_after_reading_the_clock(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        original=self.engine.rpc
        def transition(method,params):
            result=original(method,params)
            if method=='Player.GetProperties' and 'canseek' in params['properties']:self.player.position=1
            return result
        self.engine.rpc=transition
        with self.assertRaisesRegex(TrialUnavailable,'track-changed-before-seek'):session.seek(10)
        self.assertFalse(any(m=='Player.Seek' for m,p in self.player.calls))
        self.engine.rpc=original;session.close()

    def test_close_waits_for_inflight_seek_before_owned_stop(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        entered=threading.Event();release=threading.Event();original=self.engine.rpc
        def delayed(method,params):
            if method=='Player.Seek':entered.set();release.wait(2)
            return original(method,params)
        self.engine.rpc=delayed
        seeker=threading.Thread(target=lambda:session.seek(10));seeker.start()
        self.assertTrue(entered.wait(2))
        closer=threading.Thread(target=session.close);closer.start()
        self.assertTrue(closer.is_alive());release.set();seeker.join(2);closer.join(2)
        self.assertFalse(seeker.is_alive());self.assertFalse(closer.is_alive())
        self.assertEqual(self.player.ids,[]);self.assertIsNone(self.player.position)

    def test_native_seek_resume_is_explicitly_repaused_not_reseeked(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        session.pause(False);original=self.engine.rpc
        def native(method,params):
            result=original(method,params)
            if method=='Player.Seek':self.player.speed=1
            return result
        self.engine.rpc=native;begin=len(self.player.calls);session.seek(10)
        changes=[(method,params) for method,params in self.player.calls[begin:]
                 if method in ('Player.Seek','Player.PlayPause')]
        self.assertEqual(changes,[('Player.Seek',{'playerid':0,'value':{'seconds':10}}),
                                  ('Player.PlayPause',{'playerid':0,'play':False})])
        self.assertEqual(self.player.speed,0);self.assertEqual(self.player.elapsed,35000)
        session.close()

    def test_scrub_commits_one_owned_percentage_seek_and_preserves_native_pause(self):
        from music_scrub import ScrubPreview
        from music_queue import QueueSnapshot
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join();session.pause(False)
        preview=ScrubPreview.start(QueueSnapshot(session.selected,0),180000,25000).adjust(1)
        original=self.engine.rpc
        def native(method,params):
            result=original(method,params)
            if method=='Player.Seek':self.player.speed=1
            return result
        self.engine.rpc=native;begin=len(self.player.calls);session.seek_to(preview)
        self.assertAlmostEqual(self.player.elapsed,30000,delta=2);self.assertEqual(self.player.speed,0)
        writes=[(m,p) for m,p in self.player.calls[begin:] if m in ('Player.Seek','Player.PlayPause')]
        self.assertEqual(writes,[('Player.Seek',{'playerid':0,'value':{'percentage':preview.percentage}}),
                                 ('Player.PlayPause',{'playerid':0,'play':False})])
        session.close()

    def test_scrub_refuses_changed_song_order_duration_and_unseekable_source(self):
        from music_scrub import ScrubPreview
        from music_queue import QueueSnapshot
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        preview=ScrubPreview.start(QueueSnapshot(session.selected,0),180000,25000)
        self.player.position=1
        with self.assertRaisesRegex(TrialUnavailable,'stale'):session.seek_to(preview)
        self.player.position=0;self.player.duration=190000
        with self.assertRaisesRegex(TrialUnavailable,'stale'):session.seek_to(preview)
        self.player.duration=180000;self.player.canseek=False
        with self.assertRaisesRegex(TrialUnavailable,'stale'):session.seek_to(preview)
        self.assertFalse(any(m=='Player.Seek' for m,p in self.player.calls));session.close()

    def test_ready_session_remove_updates_complete_intent_and_current_position(self):
        session=self.make(4);session.start([1,2,3,4],confirmed=True);session.worker.join()
        session.select(2);session.pause(False);before=self.engine.observe()
        session.remove(0,expected_queue=before.fingerprint)
        self.assertEqual(session.selected,(2,3,4));self.assertEqual(self.player.position,1)
        self.assertEqual(self.journal[-1][0].song_ids,(2,3,4))
        self.assertEqual(session.status()['loaded'],3);session.close()

    def test_ready_shuffle_updates_queue_order_and_exit_restores_native_mode(self):
        session=self.make(4);session.start([1,2,1,4],confirmed=True);session.worker.join();session.pause(False)
        state=session.engine.observe()
        shuffled=session.set_shuffle(True,expected_queue=state.fingerprint,confirmed=True)
        self.assertEqual(session.selected,shuffled.song_ids);self.assertEqual(session.selected,(4,1,2,1))
        self.assertEqual(self.player.speed,0);self.assertEqual(session.status()['phase'],'ready')
        session.close();self.assertFalse(self.player.shuffled);self.assertEqual(self.player.ids,[])

    def test_loading_shuffle_refuses_without_a_mode_write(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        session.update(phase='loading');start=len(self.player.calls)
        with self.assertRaisesRegex(TrialUnavailable,'queue-still-loading'):
            session.set_shuffle(True,expected_queue=self.engine.observe().fingerprint,confirmed=True)
        self.assertFalse(any(m=='Player.SetShuffle' for m,p in self.player.calls[start:]));session.close()

    def test_queue_edit_during_loading_is_explicitly_refused(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        session.update(phase='loading')
        with self.assertRaisesRegex(TrialUnavailable,'queue-still-loading'):session.remove(2,expected_queue=self.engine.observe().fingerprint)
        session.update(phase='ready');session.close()

    def test_explicit_clear_stops_owned_player_then_records_empty_intent(self):
        session=self.make(3);session.start([1,2,3],confirmed=True);session.worker.join()
        state=self.engine.observe()
        with self.assertRaisesRegex(TrialUnavailable,'clear-confirmation-required'):session.clear(expected_queue=state.fingerprint)
        with self.assertRaisesRegex(TrialUnavailable,'queue-preview-stale'):session.clear(expected_queue='old',confirmed=True)
        self.assertIsNotNone(self.player.position)
        session.clear(expected_queue=state.fingerprint,confirmed=True)
        self.assertIsNone(self.player.position);self.assertEqual(self.player.ids,[])
        self.assertEqual(session.selected,());self.assertEqual(self.journal[-1][0].song_ids,())
        self.assertEqual(session.status()['phase'],'cleared');session.close()


if __name__=='__main__':unittest.main()
