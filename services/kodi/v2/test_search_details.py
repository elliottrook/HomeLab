import unittest
from global_search import Hit,SearchUnavailable,SOURCES
from search_details import read_details,DETAILS

class SearchDetailsTests(unittest.TestCase):
    def fixture(self,kind):
        source=next(s for s in SOURCES if s.kind==kind)
        row={source.identity:5,'label':'Title'}
        calls=[]
        def rpc(method,params):
            calls.append((method,params));return {DETAILS[kind][1]:dict(row)}
        return row,calls,rpc

    def test_five_types_read_twice_without_paths_or_actions(self):
        for kind in DETAILS:
            row,calls,rpc=self.fixture(kind)
            row.update(file='private-stream',token='secret')
            row[DETAILS[kind][2]]='A synopsis';row['thumbnail']='image://local-cover/'
            detail=read_details(rpc,Hit(kind,5,'Title',''))
            self.assertEqual(detail.synopsis,'A synopsis')
            self.assertEqual(len(calls),2)
            self.assertEqual({method for method,params in calls},{DETAILS[kind][0]})
            self.assertNotIn('private-stream',repr(detail));self.assertNotIn('secret',repr(detail))
            self.assertNotIn('file',calls[0][1]['properties'])

    def test_stale_id_title_and_metadata_fail_closed(self):
        for change in ({'tvshowid':6},{'label':'Renamed'},{'year':2026}):
            row,_,rpc=self.fixture('tvshow');row.update(change)
            with self.assertRaises(SearchUnavailable):read_details(rpc,Hit('tvshow',5,'Title',''))

    def test_no_synopsis_is_truthful(self):
        _,_,rpc=self.fixture('album')
        self.assertIn('not available',read_details(rpc,Hit('album',5,'Title','')).synopsis)

    def test_different_second_read_rejected(self):
        row,calls,base=self.fixture('movie')
        def rpc(method,params):
            row['plot']='First' if not calls else 'Changed'
            return base(method,params)
        with self.assertRaises(SearchUnavailable):read_details(rpc,Hit('movie',5,'Title',''))

    def test_safe_error_and_invalid_metadata(self):
        def rpc(*a):raise RuntimeError('private-error-url')
        with self.assertRaisesRegex(SearchUnavailable,'^result-unavailable$'):read_details(rpc,Hit('song',5,'Title',''))
        for change in ({'plot':{}},{'thumbnail':[]},{'plot':'a'*100001}):
            row,_,rpc=self.fixture('movie');row.update(change)
            with self.assertRaises(SearchUnavailable):read_details(rpc,Hit('movie',5,'Title',''))

    def test_boolean_or_unknown_identity_rejected_without_reads(self):
        for hit in (Hit('song',True,'Title',''),Hit('song',0,'Title',''),Hit('other',1,'Title',''),None):
            with self.assertRaises(SearchUnavailable):read_details(lambda *a:self.fail(),hit)

if __name__=='__main__':unittest.main()
