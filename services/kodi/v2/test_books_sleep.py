import unittest
from books_progress import Scope,ProgressUnavailable
from books_sleep import SleepTimer,Listening

class SleepTests(unittest.TestCase):
    def setUp(self):
        self.now=0.;self.context=Listening(Scope('house','audiobook','book'),'private-first')
        self.calls=[];self.status=[]
        self.timer=SleepTimer(lambda:self.context,self.save,self.stop,lambda s,t:self.status.append((s,t)),clock=lambda:self.now)
    def save(self,url):self.calls.append(('save',url));return True
    def stop(self,url):self.calls.append(('stop',url));return True
    def test_expiry_saves_before_single_stop_and_never_replays(self):
        self.timer.arm(15);self.now=899;self.timer.tick();self.assertFalse(self.calls)
        self.now=900;self.timer.tick();self.timer.tick()
        self.assertEqual(self.calls,[('save','private-first'),('stop','private-first')]);self.assertEqual(self.timer.state,'stopped')
    def test_file_transition_keeps_same_book_timer(self):
        self.timer.arm(15);self.context=Listening(self.context.scope,'private-second');self.now=901;self.timer.tick()
        self.assertEqual(self.calls,[('save','private-second'),('stop','private-second')])
    def test_other_book_podcast_episode_or_account_never_stopped(self):
        for scope in (Scope('house','audiobook','other'),Scope('other','audiobook','book'),Scope('house','podcast','show','two')):
            with self.subTest(scope=scope):
                self.context=Listening(Scope('house','podcast','show','one'),'one')
                self.timer.arm(15);self.context=Listening(scope,'foreign');self.now+=901;self.timer.tick()
                self.assertFalse(self.calls);self.assertEqual(self.timer.state,'off')
    def test_stopped_playback_cancels(self):
        self.timer.arm(15);self.context=None;self.now=901;self.timer.tick();self.assertFalse(self.calls)
    def test_pause_counts_wall_clock_without_media_time(self):
        self.timer.arm(30);self.now=1801;self.timer.tick();self.assertEqual(len(self.calls),2)
    def test_unknown_sample_defers_action_until_positive_ownership(self):
        self.timer.arm(15);self.now=901;self.timer.tick(known=False);self.assertFalse(self.calls)
        self.timer.tick();self.assertEqual(len(self.calls),2)
    def test_ownership_change_during_save_never_stops_foreign_media(self):
        def save(url):self.calls.append(('save',url));self.context=Listening(self.context.scope,'replaced')
        self.timer.save=save;self.timer.arm(15);self.now=901;self.timer.tick()
        self.assertEqual(self.calls,[('save','private-first')]);self.assertEqual(self.timer.state,'off')
    def test_failed_save_still_stops_owned_audio_truthfully(self):
        def fail(url):raise RuntimeError('private-detail')
        self.timer.save=fail;self.timer.arm(15);self.now=901;self.timer.tick()
        self.assertEqual(self.calls,[('stop','private-first')]);self.assertIn('not saved',self.status[-1][1])
        self.assertNotIn('private-detail',str(self.status))
    def test_uncertain_stop_is_consumed_without_retry(self):
        def fail(url):self.calls.append(('stop',url));raise RuntimeError('private-detail')
        self.timer.stop=fail;self.timer.arm(15);self.now=901;self.timer.tick();self.timer.tick()
        self.assertEqual(len(self.calls),2);self.assertEqual(self.timer.state,'uncertain')
        self.assertNotIn('private-detail',str(self.status))
    def test_cancel_reset_and_restart_have_no_expired_replay(self):
        self.timer.arm(15);self.now=60;self.assertEqual(self.timer.remaining(),840)
        self.timer.arm(30);self.assertEqual(self.timer.remaining(),1800)
        self.timer.cancel();self.now=99999;self.timer.tick();self.assertFalse(self.calls)
        fresh=SleepTimer(lambda:self.context,self.save,self.stop,lambda *a:None,clock=lambda:self.now)
        fresh.tick();self.assertFalse(self.calls)
    def test_invalid_presets_or_unowned_playback_cannot_arm(self):
        for value in (True,0,-1,5,15.0,900,'15'):
            with self.assertRaises(ProgressUnavailable):self.timer.arm(value)
        self.context=None
        with self.assertRaises(ProgressUnavailable):self.timer.arm(15)
