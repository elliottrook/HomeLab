import json,tempfile,unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from books_progress import Scope,Progress,ProgressUnavailable,timeline
from books_progress_reader import Account
from books_sync import Binding,Registry,Writer,Observer

class SyncTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.directory=Path(temp.name)/'journal'
        self.now=[0.];self.account=Account('shared','user',False,tuple((k,False) for k in ('update','delete','upload')))
        self.scope=Scope('shared','audiobook','book');self.progress=None;self.failure=False;self.calls=[];self.patch_error=False;self.bad_ack=False
        self.reader=SimpleNamespace(account=lambda:self.account,progress=self.read)
        self.writer=Writer(self.reader,self.patch,self.directory,self.account.fingerprint)
        self.registry=Registry(clock=lambda:self.now[0]);self.binding=Binding(self.scope,timeline([100]),0,0,False,1000)
        self.registry.add('owned-private-stream',self.binding);self.status=[];self.seeks=[]
        self.observer=Observer(self.registry,self.writer,lambda u,p:self.seeks.append((u,p)),lambda s,t:self.status.append((s,t)),clock=lambda:self.now[0])
    def read(self,*args):
        if self.failure:raise RuntimeError('token=secret')
        return self.progress
    def patch(self,scope,payload):
        self.calls.append((scope,payload))
        if self.patch_error:raise TimeoutError('https://private?secret')
        if not self.bad_ack:self.progress=Progress(scope,payload['duration'],payload['currentTime'],False,False,(self.progress.updated_ms+1 if self.progress else 1))
        return True
    def tick(self,pos,paused=False):self.observer.tick('owned-private-stream',pos,100,paused)
    def test_periodic_and_pause_and_stop_each_save_real_position(self):
        self.tick(0);self.now[0]=16;self.tick(16)
        self.assertEqual(self.progress.position,16)
        self.tick(20,True);self.assertEqual(self.progress.position,20)
        self.tick(20,True);self.assertEqual(len(self.calls),2)
        self.tick(22);self.observer.tick(None)
        self.assertEqual(self.progress.position,22);self.assertEqual(len(self.calls),3)
        self.assertEqual(self.observer.phase,'idle')
    def test_resume_uses_fresh_server_position_not_old_list_offset(self):
        self.progress=Progress(self.scope,100,40,False,False,1)
        self.registry.rows['owned-private-stream']=replace(self.binding,resume=True,offset=20)
        self.tick(0);self.assertEqual(self.seeks,[('owned-private-stream',40)])
        self.tick(0);self.assertEqual(len(self.seeks),1);self.tick(40)
        self.assertEqual(self.observer.phase,'ready');self.assertFalse(self.calls)
    def test_explicit_chapter_keeps_its_offset_instead_of_resume(self):
        self.progress=Progress(self.scope,100,70,False,False,1)
        self.registry.rows['owned-private-stream']=replace(self.binding,offset=30)
        self.tick(0);self.assertEqual(self.seeks[-1][1],30);self.tick(30);self.tick(35,True)
        self.assertEqual(self.progress.position,35)
    def test_other_media_not_observed_or_sought(self):
        self.observer.tick('music-not-owned',20,100);self.assertFalse(self.calls);self.assertFalse(self.seeks)
        self.assertIsNone(self.observer.url)
    def test_external_takeover_flushes_only_last_positive_book_sample(self):
        self.tick(0);self.tick(8);self.observer.tick('other-music',900,1000)
        self.assertEqual(self.progress.position,8);self.assertIsNone(self.observer.url)
    def test_unknown_observation_does_not_fake_stop(self):
        self.tick(0);self.tick(8);self.observer.tick(None,known=False)
        self.assertFalse(self.calls);self.assertEqual(self.observer.phase,'ready')
    def test_external_revision_conflict_never_overwritten(self):
        self.tick(0);self.progress=Progress(self.scope,100,60,False,False,100)
        self.tick(8,True);self.assertFalse(self.calls);self.assertEqual(self.observer.phase,'conflict')
        self.observer.tick(None);self.assertEqual(self.progress.position,60)
    def test_uncertain_write_fenced_across_service_restart(self):
        self.tick(0);self.patch_error=True;self.tick(8,True)
        self.assertEqual(self.observer.phase,'uncertain');self.assertEqual(len(self.calls),1)
        self.observer.tick(None);self.patch_error=False;self.progress=None
        self.tick(0);self.tick(10,True);self.assertEqual(len(self.calls),1)
        ledger=json.loads(next(self.directory.glob('*.json')).read_text());self.assertEqual(ledger['status'],'uncertain')
        self.assertNotIn('secret',str(ledger))
    def test_completed_title_is_playback_only_never_reset(self):
        self.progress=Progress(self.scope,100,90,True,False,100)
        self.tick(0);self.tick(8,True);self.observer.tick(None)
        self.assertFalse(self.calls);self.assertTrue(self.progress.finished)
    def test_wrong_duration_bad_start_and_end_do_not_create_progress(self):
        self.observer.tick('owned-private-stream',0,50);self.assertFalse(self.calls);self.assertEqual(self.observer.phase,'arming')
        self.now[0]=11;self.observer.tick('owned-private-stream',0,50);self.assertEqual(self.observer.phase,'unsynced')
    def test_transient_decoder_duration_settles_before_saving(self):
        self.observer.tick('owned-private-stream',0,40);self.assertEqual(self.observer.phase,'arming')
        self.now[0]=1;self.tick(0);self.assertEqual(self.observer.phase,'ready')
        self.tick(8,True);self.assertEqual(self.progress.position,8)
    def test_failed_resume_seek_is_not_retried_and_never_saves(self):
        self.progress=Progress(self.scope,100,40,False,False,1)
        self.registry.rows['owned-private-stream']=replace(self.binding,resume=True)
        self.tick(0);self.now[0]=11;self.tick(0)
        self.assertEqual(self.observer.phase,'unsynced');self.assertEqual(len(self.seeks),1);self.assertFalse(self.calls)
    def test_no_offline_replay_or_completion_from_end_seek(self):
        self.tick(0);self.failure=True;self.tick(8,True);self.failure=False;self.tick(9,False);self.tick(10,True)
        self.assertFalse(self.calls);self.assertEqual(self.observer.phase,'unsynced')
    def test_end_does_not_mark_complete(self):
        self.tick(0);self.tick(100,True);self.observer.tick(None);self.assertFalse(self.calls)
    def test_successful_verified_ledger_allows_later_real_save(self):
        first=self.writer.save(self.binding,None,8);second=self.writer.save(self.binding,first,12)
        self.assertEqual(second.position,12);self.assertEqual(len(self.calls),2)
        self.assertEqual(json.loads(next(self.directory.glob('*.json')).read_text())['status'],'verified')
    def test_unverified_write_never_repeated(self):
        self.bad_ack=True
        with self.assertRaisesRegex(ProgressUnavailable,'uncertain'):self.writer.save(self.binding,None,8)
        with self.assertRaisesRegex(ProgressUnavailable,'review'):self.writer.save(self.binding,None,8)
        self.assertEqual(len(self.calls),1)
    def test_wrong_account_missing_binding_expiry_and_private_ledger(self):
        self.account=replace(self.account,identity='other')
        with self.assertRaises(ProgressUnavailable):self.writer.read(self.scope)
        self.now[0]=1001;self.assertIsNone(self.registry.get('owned-private-stream'))
        self.assertEqual(self.directory.stat().st_mode&0o777,0o700)
    def test_multifile_transition_and_restart_save_whole_book_position(self):
        spans=timeline([100,150]);first=replace(self.binding,spans=spans)
        second=replace(first,index=1)
        self.registry.rows['owned-private-stream']=first
        self.registry.add('second-private-stream',second)
        self.tick(0);self.tick(98)
        self.observer.tick('second-private-stream',0,150)
        self.assertEqual(self.progress.position,98)
        self.observer.tick('second-private-stream',12,150,True)
        self.assertEqual(self.progress.position,112);self.assertEqual(self.progress.duration,250)
        self.observer.tick(None)
        self.registry.rows['second-private-stream']=replace(second,resume=True)
        self.observer.tick('second-private-stream',0,150)
        self.assertEqual(self.seeks[-1],('second-private-stream',12))
        self.observer.tick('second-private-stream',12,150)
        self.assertEqual(self.observer.phase,'ready')
    def test_resume_moved_to_another_file_never_guesses(self):
        self.registry.rows['owned-private-stream']=replace(self.binding,spans=timeline([100,150]),resume=True)
        self.progress=Progress(self.scope,250,130,False,False,1)
        self.tick(0);self.assertEqual(self.observer.phase,'unsynced')
        self.assertFalse(self.seeks);self.assertFalse(self.calls)
