import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from books_progress import ProgressUnavailable
from books_progress_reader import Account
from books_bookmark_trial import Bookmark,State,BookmarkTrial,project

class BookmarkTrialTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)/'trial'
        self.account='a'*64;self.progress='b'*64
        self.existing=Bookmark('other',10,'Family bookmark',1000)
        self.rows=[self.existing];self.calls=[];self.reads=0;self.on_read=None
        self.trial=BookmarkTrial(self.read,self.create,self.remove,self.root,self.account,'book',23,'Aster lab bookmark unique')
    def read(self):
        self.reads+=1
        if self.on_read:self.on_read(self.reads)
        return State(self.account,tuple(sorted(self.rows)),self.progress)
    def create(self,item,payload):
        self.calls.append('create');row=Bookmark(item,payload['time'],payload['title'],2000);self.rows.append(row);return row.row()
    def remove(self,row):self.calls.append('remove');self.rows.remove(row);return True
    def journal(self):return json.loads((self.root/'journal.json').read_text())['status']
    def test_one_create_readback_delete_preserves_existing_and_progress(self):
        before=self.read();result=self.trial.run()
        self.assertTrue(result['passed']);self.assertEqual(self.read(),before)
        self.assertEqual(self.calls,['create','remove']);self.assertEqual(self.journal(),'verified-cleaned')
        self.assertEqual((self.root/'before-private.json').stat().st_mode&0o777,0o600)
        self.assertEqual(self.root.stat().st_mode&0o777,0o700)
    def test_consumed_trial_never_repeats_even_after_success(self):
        self.trial.run()
        with self.assertRaises(FileExistsError):self.trial.run()
        self.assertEqual(self.calls,['create','remove'])
    def test_collision_before_create_never_writes(self):
        self.rows.append(Bookmark('book',23,'Someone else',1000))
        with self.assertRaisesRegex(ProgressUnavailable,'collision'):self.trial.run()
        self.assertFalse(self.calls);self.assertFalse(self.root.exists())
    def test_account_change_refused(self):
        self.account='c'*64
        with self.assertRaisesRegex(ProgressUnavailable,'account'):self.trial.run()
        self.assertFalse(self.calls)
    def test_preflight_concurrent_bookmark_change_refuses_post(self):
        def change(n):
            if n==2:self.rows.append(Bookmark('book',23,'Other client',1000))
        self.on_read=change
        with self.assertRaisesRegex(ProgressUnavailable,'preflight'):self.trial.run()
        self.assertFalse(self.calls);self.assertEqual(self.journal(),'prepared')
    def test_unknown_create_never_retries_or_deletes(self):
        def uncertain(item,payload):self.create(item,payload);raise TimeoutError('private bearer data')
        self.trial.create=uncertain
        with self.assertRaisesRegex(ProgressUnavailable,'create-uncertain'):self.trial.run()
        self.assertEqual(self.calls,['create']);self.assertEqual(self.journal(),'uncertain-create')
        self.assertNotIn('bearer',(self.root/'journal.json').read_text())
        with self.assertRaises(Exception):self.trial.run()
        self.assertEqual(self.calls,['create'])
    def test_wrong_echo_never_authorizes_cleanup(self):
        def wrong(item,payload):row=self.create(item,payload);return dict(row,time=24)
        self.trial.create=wrong
        with self.assertRaisesRegex(ProgressUnavailable,'create-uncertain'):self.trial.run()
        self.assertEqual(self.calls,['create'])
    def test_changed_bookmark_before_cleanup_retained_for_review(self):
        def change(n):
            if n==4:self.rows[-1]=Bookmark('book',23,'Changed on another client',2000)
        self.on_read=change
        with self.assertRaisesRegex(ProgressUnavailable,'cleanup-blocked'):self.trial.run()
        self.assertEqual(self.calls,['create']);self.assertEqual(self.journal(),'cleanup-blocked')
    def test_progress_changed_before_cleanup_no_delete_or_repair(self):
        def change(n):
            if n==4:self.progress='d'*64
        self.on_read=change
        with self.assertRaisesRegex(ProgressUnavailable,'cleanup-blocked'):self.trial.run()
        self.assertEqual(self.calls,['create']);self.assertEqual(self.progress,'d'*64)
    def test_changed_existing_bookmark_after_create_aborts(self):
        def change(n):
            if n==3:self.rows[0]=Bookmark('other',10,'Changed elsewhere',1000)
        self.on_read=change
        with self.assertRaisesRegex(ProgressUnavailable,'create-uncertain'):self.trial.run()
        self.assertEqual(self.calls,['create'])
    def test_unknown_delete_consumed_no_retries(self):
        def uncertain(row):self.remove(row);raise TimeoutError('private response')
        self.trial.remove=uncertain
        with self.assertRaisesRegex(ProgressUnavailable,'delete-uncertain'):self.trial.run()
        self.assertEqual(self.journal(),'uncertain-delete');self.assertEqual(self.calls,['create','remove'])
        with self.assertRaises(FileExistsError):self.trial.run()
        self.assertEqual(self.calls,['create','remove'])
    def test_unacknowledged_delete_not_success(self):
        self.trial.remove=lambda row:False
        with self.assertRaisesRegex(ProgressUnavailable,'delete-uncertain'):self.trial.run()
        self.assertEqual(self.journal(),'uncertain-delete')
    def test_changed_final_progress_is_not_silently_restored(self):
        def change(n):
            if n==5:self.progress='e'*64
        self.on_read=change
        with self.assertRaisesRegex(ProgressUnavailable,'delete-uncertain'):self.trial.run()
        self.assertEqual(self.progress,'e'*64)
    def test_invalid_scope_times_and_labels_rejected(self):
        for time in (True,-1,0,604800,23.0):
            with self.assertRaises(ProgressUnavailable):BookmarkTrial(self.read,self.create,self.remove,self.root,self.account,'book',time,'Aster lab bookmark unique')
        with self.assertRaises(ProgressUnavailable):BookmarkTrial(self.read,self.create,self.remove,self.root,self.account,'../unsafe',23,'Aster lab bookmark unique')
    def test_projection_excludes_secret_fields_and_tracks_progress(self):
        account=Account('shared','user',False,tuple((k,False) for k in ('download','update','delete','upload')))
        raw=dict(id='shared',token='SECRET',username='PRIVATE',bookmarks=[self.existing.row()],mediaProgress=[dict(libraryItemId='book',currentTime=42,token='SECRET')])
        reader=SimpleNamespace(account=lambda:account,_get=lambda path:copy.deepcopy(raw))
        before=project(reader,account.fingerprint)
        self.assertNotIn('SECRET',json.dumps(before.row()));self.assertNotIn('PRIVATE',json.dumps(before.row()))
        raw['mediaProgress'][0]['currentTime']=43;self.assertNotEqual(project(reader,account.fingerprint).progress_sha256,before.progress_sha256)
    def test_duplicate_bookmark_identity_rejected(self):
        with self.assertRaises(ProgressUnavailable):State(self.account,(self.existing,self.existing),self.progress)
