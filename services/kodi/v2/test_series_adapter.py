import copy,unittest
from series_adapter import read_series,SeriesUnavailable,READS
from test_series_model import episode

class Library:
    def __init__(self,rows=None):self.rows=rows if rows is not None else [episode()];self.calls=[];self.pass_number=0
    def __call__(self,method,params):
        self.calls.append((method,copy.deepcopy(params)))
        if method=='VideoLibrary.GetTVShowDetails':
            self.pass_number+=1
            return {'tvshowdetails':dict(tvshowid=12,title='Synthetic series',genre=['Drama'],year=2020,
                rating=8.2,art={'fanart':'fixture-fanart'})}
        start=params['limits']['start'];end=min(params['limits']['end'],len(self.rows))
        return dict(episodes=copy.deepcopy(self.rows[start:end]),limits=dict(start=start,end=end,total=len(self.rows)))

class SeriesAdapterTests(unittest.TestCase):
    def test_complete_paginated_double_read_and_accepted_next(self):
        source=Library([episode(1,playcount=1),episode(2,1,2),episode(3,1,3)])
        calls=[]
        def next_up(show,rows,**kwargs):calls.append(rows);return rows[1]
        result=read_series(source,12,next_up,page_size=2,today='2026-10-24')
        self.assertEqual(result.page.primary_episode_id,2);self.assertEqual(len(calls),1)
        self.assertEqual(source.pass_number,2);self.assertEqual(len(source.calls),6)
        self.assertLessEqual({m for m,p in source.calls},READS)
        self.assertEqual(result.title,'Synthetic series');self.assertEqual(result.fanart,'fixture-fanart')
        self.assertFalse(hasattr(result.page.seasons[0].episodes[0],'file'))

    def test_empty_series_has_safe_escape(self):
        result=read_series(Library([]),12,lambda *a,**k:None)
        self.assertIsNone(result.page.restore())

    def test_truncation_and_malformed_page_refused(self):
        for bad in ({'limits':dict(start=0,end=1,total=2),'episodes':[]},
                    {'limits':dict(start=0,end=0,total=2),'episodes':[]},
                    {'limits':dict(start=False,end=1,total=1),'episodes':[episode()]},
                    {'limits':dict(start=0,end=1,total=True),'episodes':[episode()]}, []):
            base=Library()
            def rpc(method,params):return base(method,params) if method.endswith('Details') else bad
            with self.subTest(bad=bad),self.assertRaises(SeriesUnavailable):read_series(rpc,12,lambda *a,**k:None)

    def test_changing_snapshot_and_show_identity_refused(self):
        for key,value in (('label','Changed'),('tvshowid',99)):
            source=Library()
            def rpc(method,params):
                result=source(method,params)
                if method.endswith('GetEpisodes') and source.pass_number==2:result['episodes'][0][key]=value
                return result
            with self.assertRaises(SeriesUnavailable):read_series(rpc,12,lambda *a,**k:None)

    def test_mixed_show_duplicate_and_invalid_watch_state_checked_before_policy(self):
        for rows in ([dict(episode(),tvshowid=99)],[episode(),episode()],[episode(playcount=True)]):
            called=[]
            with self.assertRaises(SeriesUnavailable):read_series(Library(rows),12,lambda *a,**k:called.append(True))
            self.assertEqual(called,[])

    def test_no_raw_rpc_error_or_unbounded_options(self):
        def unavailable(*args):raise RuntimeError('synthetic-sensitive-value')
        with self.assertRaisesRegex(SeriesUnavailable,'^series-read-unavailable$'):read_series(unavailable,12,None)
        for values in ({'show_id':True},{'page_size':0},{'cap':10001}):
            params=dict(show_id=12);params.update(values)
            with self.assertRaises(SeriesUnavailable):read_series(Library(),next_up=lambda *a,**k:None,**params)

    def test_policy_failure_is_not_replaced_by_new_sequencing_guess(self):
        def unavailable(*a,**k):raise ValueError()
        with self.assertRaisesRegex(SeriesUnavailable,'accepted-up-next-unavailable'):
            read_series(Library(),12,unavailable)

    def test_policy_input_mutation_does_not_modify_snapshot(self):
        source=Library([episode(1,playcount=1),episode(2,1,2)])
        def policy(show,rows,**kwargs):rows.clear();show.clear();return None
        result=read_series(source,12,policy)
        self.assertEqual(len(result.page.seasons[0].episodes),2)
        self.assertEqual(result.title,'Synthetic series')
