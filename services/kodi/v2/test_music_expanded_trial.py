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


if __name__=='__main__':unittest.main()
