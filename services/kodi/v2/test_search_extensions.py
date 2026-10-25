import unittest
from types import SimpleNamespace
from global_search import Hit, SearchUnavailable
from search_extensions import artist_albums, movie_info_item


class SearchExtensionsTests(unittest.TestCase):
    def response(self, ids=(1, 2), total=None, start=0):
        return dict(limits=dict(start=start, end=start+len(ids), total=len(ids) if total is None else total),
                    albums=[dict(albumid=i, title='Album', artist=['Artist'], year=2020) for i in ids])

    def test_artist_uses_exact_id_and_projects_display_only(self):
        calls=[]
        def rpc(method, params):
            calls.append((method, params))
            value=self.response();value['albums'][0]['file']='must-not-escape'
            return value
        result=artist_albums(rpc, 9)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(m=='AudioLibrary.GetAlbums' and p['filter']==dict(artistid=9) for m,p in calls))
        self.assertEqual(result['hits'][0], Hit('album', 1, 'Album', 'Artist · 2020'))
        self.assertNotIn('must-not-escape', repr(result))
        self.assertFalse(result['truncated'])

    def test_empty_is_truthful(self):
        self.assertEqual(artist_albums(lambda *_:self.response(()), 1), dict(hits=(), total=0, truncated=False))

    def test_truncation_and_paging(self):
        calls=[]
        def rpc(_, params):
            start=params['limits']['start'];calls.append(start)
            return self.response((start+1,), total=4, start=start)
        result=artist_albums(rpc, 1, page_size=1, cap=2)
        self.assertEqual(calls, [0,1,0,1]);self.assertTrue(result['truncated'])
        self.assertEqual(result['total'], 4)

    def test_reject_bad_identity_options_and_cancellation(self):
        for value in (True, 0, -1, '1', 2147483648):
            with self.assertRaises(SearchUnavailable):artist_albums(lambda *_:None, value)
        for options in (dict(page_size=True),dict(cap=99),dict(page_size=201)):
            with self.assertRaises(SearchUnavailable):artist_albums(lambda *_:None, 1, **options)
        with self.assertRaisesRegex(SearchUnavailable, 'cancelled'):
            artist_albums(lambda *_:None, 1, cancelled=lambda:True)

    def test_unavailable_duplicate_malformed_and_changing(self):
        def broken(*_):raise RuntimeError('private')
        with self.assertRaisesRegex(SearchUnavailable, '^artist-albums-unavailable$'):artist_albums(broken, 1)
        for response in (None, {}, self.response((1,1)), self.response((True,)),
                         dict(limits=dict(start=0,end=0,total=3))):
            with self.assertRaises(SearchUnavailable):artist_albums(lambda *_:response, 1)
        rows=iter((self.response((1,)),self.response((2,))))
        with self.assertRaisesRegex(SearchUnavailable, 'artist-albums-changed'):artist_albums(lambda *_:next(rows), 1)

    def test_movie_item_has_identity_but_no_guessed_path_or_play(self):
        calls=[]
        class Tag:
            def setDbId(self, v):calls.append(('id',v))
            def setMediaType(self, v):calls.append(('type',v))
            def setTitle(self, v):calls.append(('title',v))
        class Item:
            def __init__(self, **kwargs):calls.append(('item',kwargs))
            def getVideoInfoTag(self):return Tag()
        gui=SimpleNamespace(ListItem=Item)
        movie_info_item(gui, Hit('movie', 42, 'Title,(not a command)', '2020'))
        self.assertEqual(calls[1:], [('id',42),('type','movie'),('title','Title,(not a command)')])
        for hit in (Hit('movie',True,'T',''),Hit('album',1,'T',''),None):
            with self.assertRaises(SearchUnavailable):movie_info_item(gui, hit)


if __name__=='__main__':unittest.main()
