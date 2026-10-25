import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from books_progress import Scope,Draft,Progress,ProgressUnavailable
from books_progress_trial import TrialWriter

class TrialTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.folder=Path(temporary.name)/'writes';self.scope=Scope('tv','audiobook','book')
        self.account=SimpleNamespace(identity='tv',limited=True)
        self.saved=None;self.calls=[];self.fail=False;self.ack=True;self.bad=False
        self.reader=SimpleNamespace(account=lambda:self.account,progress=lambda *args:self.saved)
        self.draft=Draft(self.scope,100,8,False)
        self.writer=TrialWriter(self.reader,self.patch,self.folder,frozenset([self.scope]))
    def patch(self,scope,payload):
        self.calls.append((scope,payload))
        if self.fail:raise OSError('https://private?token=secret')
        if not self.bad:self.saved=Progress(scope,payload['duration'],payload['currentTime'],False,False,1000)
        return self.ack
    def test_one_new_position_verified_and_journal_private(self):
        self.assertEqual(self.writer.save_new_once(self.draft).position,8)
        path=next(self.folder.glob('*.json'));self.assertEqual(path.stat().st_mode&0o777,0o600)
        self.assertEqual(json.loads(path.read_text())['status'],'verified');self.assertEqual(len(self.calls),1)
        self.assertNotIn('secret',path.read_text())
    def test_existing_progress_never_overwritten(self):
        self.saved=Progress(self.scope,100,5,False,False,100)
        with self.assertRaisesRegex(ProgressUnavailable,'existing-progress'):self.writer.save_new_once(self.draft)
        self.assertFalse(self.calls);self.assertFalse(self.folder.exists())
    def test_unapproved_account_target_and_completion_refused(self):
        for value in (Draft(Scope('tv','audiobook','other'),100,8,False),Draft(self.scope,100,100,True),Draft(self.scope,100,0,False)):
            with self.assertRaises(ProgressUnavailable):self.writer.save_new_once(value)
        self.account.identity='other'
        with self.assertRaisesRegex(ProgressUnavailable,'account'):self.writer.save_new_once(self.draft)
        self.assertFalse(self.calls)
    def test_uncertain_ack_failure_and_readback_mismatch_never_retried(self):
        for mode in ('error','no-ack','bad-readback'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                self.writer.journal=Path(temp)/'writes';self.fail=mode=='error';self.ack=mode!='no-ack';self.bad=mode=='bad-readback';self.saved=None;self.calls=[]
                with self.assertRaisesRegex(ProgressUnavailable,'uncertain-no-retry'):self.writer.save_new_once(self.draft)
                self.saved=None
                with self.assertRaisesRegex(ProgressUnavailable,'consumed'):self.writer.save_new_once(self.draft)
                self.assertEqual(len(self.calls),1)
                self.assertEqual(json.loads(next(self.writer.journal.glob('*.json')).read_text())['status'],'uncertain')
    def test_restart_prepared_fence_is_not_replayed(self):
        self.writer.save_new_once(self.draft);path=next(self.folder.glob('*.json'));row=json.loads(path.read_text());row['status']='prepared';path.write_text(json.dumps(row));self.saved=None
        another=TrialWriter(self.reader,self.patch,self.folder,frozenset([self.scope]))
        with self.assertRaisesRegex(ProgressUnavailable,'consumed'):another.save_new_once(self.draft)
        self.assertEqual(len(self.calls),1)
    def test_public_or_linked_journal_refused(self):
        self.folder.mkdir(mode=0o755)
        with self.assertRaisesRegex(ProgressUnavailable,'private-journal'):self.writer.save_new_once(self.draft)
        self.assertFalse(self.calls)
