import json
from pathlib import Path
import tempfile
import threading
import unittest

from music_expanded_trial import ExpandedTrial, TrialCancelled, expanded_capability, save_intent
from music_queue import QueueSnapshot
from music_trial import TrialUnavailable, validate_write
from test_music_trial import FakePlayer


class ExpandedTests(unittest.TestCase):
    def test_owned_selection_navigates_exact_duplicate_without_replacing_queue(self):
        trial=self.make(3);trial.play([1,2,1,3],confirmed=True);trial.pause(False)
        start=len(self.player.calls);state=trial.select(2,expected_queue=trial.observe().fingerprint)
        self.assertEqual(state,QueueSnapshot((1,2,1,3),2));self.assertEqual(self.player.speed,1)
        writes=[m for m,p in self.player.calls[start:] if m in ('Player.Open','Player.GoTo','Player.Stop','Playlist.Clear')]
        self.assertEqual(writes,['Player.GoTo']);trial.close()

    def test_select_current_resumes_without_restart_and_stale_never_writes(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True);trial.pause(False);start=len(self.player.calls)
        with self.assertRaisesRegex(TrialUnavailable,'stale'):trial.select(1,expected_queue='stale')
        trial.select(0,expected_queue=trial.observe().fingerprint)
        self.assertEqual(self.player.elapsed,25000);self.assertEqual(self.player.speed,1)
        self.assertFalse(any(m in ('Player.GoTo','Player.Open') for m,p in self.player.calls[start:]));trial.close()
    def test_shuffle_allows_bounded_paused_clock_reporting_jitter_not_restart(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True);trial.pause(False)
        original=trial.rpc;count=[0]
        def jitter(method,params):
            result=original(method,params)
            if method=='Player.GetProperties' and 'time' in params['properties']:
                result['time']=dict(hours=0,minutes=0,seconds=25,milliseconds=(0,10,5,20)[count[0]%4]);count[0]+=1
            return result
        trial.rpc=jitter
        trial.set_shuffle(True,expected_queue=trial.observe().fingerprint,confirmed=True)
        self.assertTrue(trial.shuffled);trial.close()

    def test_shuffle_refuses_clock_still_advancing_before_any_mode_write(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True);trial.pause(False)
        original=trial.rpc
        def drifting(method,params):
            if method=='Player.GetProperties' and 'time' in params['properties']:self.player.elapsed+=300
            return original(method,params)
        trial.rpc=drifting;start=len(self.player.calls)
        with self.assertRaisesRegex(TrialUnavailable,'paused-clock-not-stable'):
            trial.set_shuffle(True,expected_queue=trial.observe().fingerprint,confirmed=True)
        self.assertFalse(trial.shuffle_uncertain)
        self.assertFalse(any(m=='Player.SetShuffle' for m,p in self.player.calls[start:]));trial.close()

    def test_shuffle_clock_reset_is_sticky_and_never_retried(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True);trial.pause(False);original=trial.rpc
        def reset(method,params):
            result=original(method,params)
            if method=='Player.SetShuffle':self.player.elapsed=0
            return result
        trial.rpc=reset
        with self.assertRaisesRegex(TrialUnavailable,'clock-changed'):
            trial.set_shuffle(True,expected_queue=trial.observe().fingerprint,confirmed=True)
        self.assertTrue(trial.shuffle_uncertain)
        self.assertEqual(sum(m=='Player.SetShuffle' for m,p in self.player.calls),1)
    def test_native_shuffle_round_trip_preserves_exact_paused_duplicate_and_order(self):
        trial=self.make(3);trial.play([1,2,1,3,2],confirmed=True)
        self.player.position=2;trial.pause(False);before=trial.observe();start=len(self.player.calls)
        shuffled=trial.set_shuffle(True,expected_queue=before.fingerprint,confirmed=True)
        self.assertEqual(shuffled.song_ids,(2,3,1,2,1));self.assertEqual(shuffled.current_index,2)
        self.assertEqual(self.player.speed,0);self.assertEqual(self.player.elapsed,25000)
        for edit in (lambda:trial.edit('append',[1]),lambda:trial.remove(0,expected_queue=shuffled.fingerprint)):
            with self.assertRaisesRegex(TrialUnavailable,'turn-shuffle-off'):edit()
        restored=trial.set_shuffle(False,expected_queue=shuffled.fingerprint,confirmed=True)
        self.assertEqual(restored,before)
        writes=[m for m,p in self.player.calls[start:] if m.startswith(('Playlist.','Player.')) and m not in
                ('Playlist.GetItems','Player.GetProperties','Player.GetItem','Player.GetActivePlayers')]
        self.assertEqual(writes,['Player.SetShuffle','Player.SetShuffle'])
        trial.close()

    def test_shuffle_confirmation_stale_or_external_mode_denies_without_mutation(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True);state=trial.observe();start=len(self.player.calls)
        with self.assertRaisesRegex(TrialUnavailable,'confirmation'):trial.set_shuffle(True,expected_queue=state.fingerprint)
        with self.assertRaisesRegex(TrialUnavailable,'stale'):trial.set_shuffle(True,expected_queue='stale',confirmed=True)
        self.player.shuffled=True
        with self.assertRaisesRegex(TrialUnavailable,'external-player-mode'):trial.set_shuffle(True,expected_queue=state.fingerprint,confirmed=True)
        self.assertFalse(any(m=='Player.SetShuffle' for m,p in self.player.calls[start:]))
        self.player.shuffled=False;trial.close()

    def test_exit_restores_shuffle_mode_even_when_cancelled_before_owned_stop(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True)
        trial.set_shuffle(True,expected_queue=trial.observe().fingerprint,confirmed=True)
        trial.cancel.set();start=len(self.player.calls);trial.close()
        writes=[m for m,p in self.player.calls[start:] if m in ('Player.SetShuffle','Player.Stop','Playlist.Clear')]
        self.assertEqual(writes,['Player.SetShuffle','Player.Stop','Playlist.Clear'])
        self.assertFalse(self.player.shuffled);self.assertEqual(self.player.ids,[])

    def test_uncertain_shuffle_is_not_retried_or_accepted(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True);original=trial.rpc
        def fail(method,params):
            if method=='Player.SetShuffle':raise OSError('unknown')
            return original(method,params)
        trial.rpc=fail
        with self.assertRaisesRegex(TrialUnavailable,'uncertain'):
            trial.set_shuffle(True,expected_queue=trial.observe().fingerprint,confirmed=True)
        self.assertFalse(trial.shuffled)
        with self.assertRaisesRegex(TrialUnavailable,'recovery-required'):trial.pause(False)
        with self.assertRaisesRegex(TrialUnavailable,'recovery-required'):trial.close()

    def test_ended_shuffled_player_restores_mode_without_reopening(self):
        for vendor_cleared in (False,True):
            trial=self.make(3);trial.play([1,2,3],confirmed=True)
            trial.set_shuffle(True,expected_queue=trial.observe().fingerprint,confirmed=True)
            self.player.position=None
            if vendor_cleared:self.player.ids=[]
            start=len(self.player.calls);trial.cancel.set();trial.close()
            self.assertFalse(self.player.shuffled);self.assertEqual(self.player.ids,[])
            self.assertFalse(any(m in ('Player.Open','Player.Stop') for m,p in self.player.calls[start:]))

    def test_ended_shuffle_never_clears_foreign_nonempty_queue(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True)
        trial.set_shuffle(True,expected_queue=trial.observe().fingerprint,confirmed=True)
        self.player.position=None;self.player.ids=[2];start=len(self.player.calls)
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):trial.close()
        self.assertEqual(self.player.ids,[2]);self.assertTrue(self.player.shuffled)
        self.assertFalse(any(m in ('Playlist.Clear','Player.SetShuffle') for m,p in self.player.calls[start:]))
    def make(self,n=430,**kwargs):
        self.player=FakePlayer();self.journal=[]
        self.trial=ExpandedTrial(self.player,list(range(1,n+1)),lambda s:True,
            queue_limit=20000,intent=lambda s,**kw:self.journal.append((s,kw)),
            sleep=lambda n:None,**kwargs)
        return self.trial

    def test_batches_exact_order_and_full_album(self):
        trial=self.make();ids=list(range(430,0,-1))
        trial.play(ids,confirmed=True)
        self.assertEqual(self.player.ids,ids)
        writes=[p for m,p in self.player.calls if m=='Playlist.Add']
        self.assertEqual([len(p['item']) for p in writes],[200,200,30])
        trial.close();self.assertEqual(self.player.ids,[])
        self.assertEqual(trial.saved.song_ids,tuple(ids))

    def test_large_queue_read_optimisation_does_not_relax_complete_order_checks(self):
        trial=self.make();trial.play(list(range(1,431)),confirmed=True)
        begin=len(self.player.calls);trial.observe()
        self.assertEqual(sum(m=='Playlist.GetItems' for m,p in self.player.calls[begin:]),2)
        self.player.ids[0],self.player.ids[1]=self.player.ids[1],self.player.ids[0]
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):trial.observe()

    def test_batch_insert_preserves_current_and_existing_suffix(self):
        trial=self.make(500);trial.play([1,500],confirmed=True)
        trial.edit('next',list(range(2,432)))
        self.assertEqual(self.player.ids,[1]+list(range(2,432))+[500])
        self.assertEqual(self.player.position,0)

    def test_cancel_before_open_restores_empty_without_start(self):
        cancel=threading.Event()
        trial=self.make(cancel=cancel,progress=lambda done,total:cancel.set())
        with self.assertRaises(TrialCancelled):trial.play(list(range(1,431)),confirmed=True)
        self.assertEqual(self.player.ids,[]);self.assertIsNone(self.player.position)
        self.assertFalse(any(m=='Player.Open' for m,p in self.player.calls))
        self.assertEqual(trial.saved.song_ids,tuple(range(1,431)))

    def test_cancel_after_open_resolves_and_stops_owned_player(self):
        cancel=threading.Event();trial=self.make(cancel=cancel)
        original=trial.rpc
        def rpc(method,p):
            result=original(method,p)
            if method=='Player.Open':cancel.set()
            return result
        trial.rpc=rpc
        with self.assertRaises(TrialCancelled):trial.play([1,2],confirmed=True)
        self.assertIsNone(self.player.position);self.assertEqual(self.player.ids,[])

    def test_foreign_queue_during_staging_is_not_overwritten(self):
        trial=self.make(progress=lambda done,total:setattr(self.player,'ids',[99999]))
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):
            trial.play(list(range(1,431)),confirmed=True)
        self.assertEqual(self.player.ids,[99999])
        self.assertEqual(sum(m=='Playlist.Add' for m,p in self.player.calls),1)

    def test_large_write_guard_retains_per_call_and_identity_limits(self):
        params={'playlistid':0,'item':[{'songid':i} for i in range(1,202)]}
        with self.assertRaises(TrialUnavailable):validate_write('Playlist.Add',params,set(range(1,300)),queue_limit=20000)
        params['item'].pop();validate_write('Playlist.Add',params,set(range(1,300)),queue_limit=20000)

    def test_atomic_intent_private_order_duplicates_and_no_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'intent.json'
            save_intent(path,QueueSnapshot((3,1,3),1),status='stopped')
            self.assertEqual(json.loads(path.read_text())['song_ids'],[3,1,3])
            self.assertEqual(path.stat().st_mode&0o777,0o600)
            save_intent(path,QueueSnapshot((2,),None),status='staged')
            self.assertEqual(json.loads(path.read_text())['song_ids'],[2])
            self.assertEqual(len(list(Path(directory).iterdir())),1)

    def test_expanded_capability_requires_explicit_limit_hp_and_short_expiry(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'approval.json'
            data={'song_ids':list(range(1,431)),'queue_limit':20000,'expires_at':200}
            path.write_text(json.dumps(data))
            self.assertEqual(expanded_capability(path,host='AsterTV',now=100),(tuple(range(1,431)),20000))
            self.assertEqual(expanded_capability(path,host='AsterTVProd',now=100),((),3))
            for change in ({'queue_limit':20001},{'queue_limit':True},{'expires_at':1901},{'extra':True}):
                path.write_text(json.dumps(dict(data,**change)))
                self.assertEqual(expanded_capability(path,host='AsterTV',now=100),((),3))
            data.pop('queue_limit');path.write_text(json.dumps(data))
            self.assertEqual(expanded_capability(path,host='AsterTV',now=100),((),3))

    def test_preexisting_queue_and_no_confirmation_still_deny_expanded_write(self):
        trial=self.make()
        with self.assertRaisesRegex(TrialUnavailable,'confirmation'):trial.play([1,2])
        self.assertFalse(any(m=='Playlist.Add' for m,p in self.player.calls))

    def test_expanded_total_limit_not_just_per_batch(self):
        trial=self.make(3);trial.queue_limit=3
        trial.edit('append',[1,2,3])
        with self.assertRaisesRegex(TrialUnavailable,'expanded-queue-limit'):trial.edit('append',[1])
        self.assertEqual(self.player.ids,[1,2,3])

    def test_saved_intent_only_replays_after_confirmation_after_vendor_clear(self):
        trial=self.make(3);trial.play([3,1,2],confirmed=True)
        trial.stop();self.player.ids=[];trial.last=QueueSnapshot((),None)
        with self.assertRaisesRegex(TrialUnavailable,'confirmation'):trial.replay()
        self.assertEqual(self.player.ids,[])
        trial.replay(confirmed=True)
        self.assertEqual(self.player.ids,[3,1,2]);self.assertEqual(self.player.position,0)

    def test_owned_remove_preserves_duplicate_occurrences_and_paused_song(self):
        trial=self.make(3);trial.play([1,2,1,3],confirmed=True)
        self.player.position=2;trial.pause(False)
        before=trial.observe();begin=len(self.player.calls)
        state=trial.remove(0,expected_queue=before.fingerprint)
        self.assertEqual(state.song_ids,(2,1,3));self.assertEqual(state.current_index,1)
        self.assertEqual(self.player.speed,0)
        self.assertFalse(any(m in ('Player.Open','Player.Stop','Playlist.Clear') for m,p in self.player.calls[begin:]))
        trial.close()

    def test_remove_current_stale_or_foreign_queue_never_writes(self):
        trial=self.make(3);trial.play([1,2,3],confirmed=True);state=trial.observe()
        start=len(self.player.calls)
        with self.assertRaisesRegex(TrialUnavailable,'queue-remove-refused'):trial.remove(0,expected_queue=state.fingerprint)
        with self.assertRaisesRegex(TrialUnavailable,'queue-preview-stale'):trial.remove(1,expected_queue='stale')
        self.player.ids=[99999]
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):trial.remove(0,expected_queue=state.fingerprint)
        self.assertFalse(any(m=='Playlist.Remove' for m,p in self.player.calls[start:]))

    def test_idle_clear_requires_confirmation_and_does_not_stop_or_open(self):
        trial=self.make(3);trial.edit('append',[1,2,3]);state=trial.observe()
        with self.assertRaisesRegex(TrialUnavailable,'queue-clear-refused'):trial.clear(expected_queue=state.fingerprint)
        begin=len(self.player.calls)
        actual=trial.clear(expected_queue=state.fingerprint,confirmed=True)
        self.assertEqual(actual.song_ids,())
        self.assertFalse(any(m in ('Player.Open','Player.Stop') for m,p in self.player.calls[begin:]))
        trial.close()


if __name__=='__main__':unittest.main()
