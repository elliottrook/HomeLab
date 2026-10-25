import io,json,unittest,urllib.error
from books_progress import ProgressUnavailable
from books_progress_reader import Reader,MAX_RESPONSE
class Reply(io.BytesIO):
    def __init__(self,row,status=200):super().__init__(json.dumps(row).encode());self.status=status
class ReaderTests(unittest.TestCase):
    def setUp(self):
        self.user=dict(id='tv-listener',type='user',isLocked=False,token='never-project',email='private',
            permissions=dict(download=True,update=False,delete=False,upload=False))
        self.row=dict(libraryItemId='book',episodeId=None,duration=100,currentTime=20,isFinished=False,lastUpdate=1000)
        self.calls=[];self.status=200
    def upstream(self,path,**kwargs):
        self.calls.append((path,kwargs))
        return Reply(self.user if path=='/api/me' else self.row,self.status)
    def test_account_projection_has_no_token_email_or_credential(self):
        account=Reader(self.upstream).account();self.assertTrue(account.limited)
        self.assertNotIn('never-project',repr(account));self.assertNotIn('private',repr(account))
        self.assertNotIn('tv-listener',repr(account));self.assertEqual(len(account.fingerprint),64)
    def test_book_read_and_account_revalidation_are_get_only(self):
        reader=Reader(self.upstream);account=reader.account();value=reader.progress(account,'audiobook','book')
        self.assertEqual(value.position,20)
        self.assertEqual([path for path,_ in self.calls],['/api/me','/api/me/progress/book','/api/me'])
        self.assertTrue(all(kwargs=={'method':'GET'} for _,kwargs in self.calls))
    def test_podcast_key_and_no_cross_episode_read(self):
        self.row.update(libraryItemId='show',episodeId='one');reader=Reader(self.upstream);account=reader.account()
        reader.progress(account,'podcast','show','one');self.assertIn('/api/me/progress/show/one',[p for p,_ in self.calls])
        with self.assertRaises(ProgressUnavailable):reader.progress(account,'podcast','show','two')
    def test_admin_and_broad_write_permissions_refuse_progress_read(self):
        original=json.loads(json.dumps(self.user))
        for mode in ('root','admin','update','delete','upload','locked'):
            user=json.loads(json.dumps(original))
            if mode in ('root','admin'):user['type']=mode
            elif mode=='locked':user['isLocked']=True
            else:user['permissions'][mode]=True
            self.user=user;reader=Reader(self.upstream);account=reader.account();before=len(self.calls)
            with self.assertRaisesRegex(ProgressUnavailable,'limited'):reader.progress(account,'audiobook','book')
            self.assertEqual(len(self.calls),before)
    def test_confirmed_404_distinct_from_timeout_and_server_errors(self):
        reader=Reader(self.upstream);account=reader.account()
        def missing(path,**kwargs):
            if path=='/api/me':return Reply(self.user)
            raise urllib.error.HTTPError('private',404,'private',{},None)
        self.assertIsNone(Reader(missing).progress(account,'audiobook','book'))
        for code in (401,403,500):
            def failure(path,**kwargs):raise urllib.error.HTTPError('token=secret',code,'private',{},None)
            with self.assertRaisesRegex(ProgressUnavailable,'^progress-service-unavailable$'):Reader(failure).progress(account,'audiobook','book')
    def test_account_switch_refused(self):
        reader=Reader(self.upstream);account=reader.account();self.user['id']='other'
        with self.assertRaisesRegex(ProgressUnavailable,'account-changed'):reader.progress(account,'audiobook','book')
    def test_invalid_id_never_reaches_transport(self):
        reader=Reader(self.upstream);account=reader.account();before=len(self.calls)
        for item in ('../me','book?x=secret','book/episode'):
            with self.assertRaises(ProgressUnavailable):reader.progress(account,'audiobook',item)
        self.assertEqual(len(self.calls),before)
    def test_mutating_get_route_and_arbitrary_endpoint_refused(self):
        reader=Reader(self.upstream);account=reader.account();before=len(self.calls)
        with self.assertRaises(ProgressUnavailable):reader.progress(account,'podcast','book','remove-from-continue-listening')
        for path in ('/api/users','/api/me/progress/book/episode/extra','/api/me/progress/book?x=y'):
            with self.assertRaises(ProgressUnavailable):reader._get(path)
        self.assertEqual(len(self.calls),before)
    def test_oversized_or_malformed_response_sanitized(self):
        for data in (b'{private',b' '+b'x'*MAX_RESPONSE):
            def broken(path,**kwargs):
                reply=io.BytesIO(data);reply.status=200;return reply
            with self.assertRaises(ProgressUnavailable):Reader(broken).account()
