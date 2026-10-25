import unittest
from copy import deepcopy
from global_search import SOURCES, SearchUnavailable, normalize_query, search, search_group


class Fake:
    def __init__(self, source=SOURCES[0], count=3):
        self.source, self.count, self.calls = source, count, []
        self.mutate = None

    def __call__(self, method, params):
        self.calls.append((method, deepcopy(params)))
        start, end = params['limits']['start'], min(params['limits']['end'], self.count)
        result = {'limits': dict(start=start, end=end, total=self.count),
                  self.source.rows: [{self.source.identity: i+1, 'label': 'Title '+str(i)}
                                     for i in range(start, end)]}
        if self.mutate:
            self.mutate(result)
        return result


class GlobalSearchTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(normalize_query('  cafe\u0301   noir '), 'café noir')
        self.assertEqual(normalize_query(''), '')
        self.assertEqual(normalize_query("x%_'\\"), "x%_'\\")
        for value in (None, 1, 'a\x00', 'a\n', 'a\u202e', 'x'*101, 'a '*9):
            with self.assertRaises(SearchUnavailable): normalize_query(value)

    def test_empty_query_never_reads(self):
        self.assertTrue(all(g.state == 'idle' for g in search(lambda *a: self.fail(), ' ')))

    def test_complete_two_reads_and_projection(self):
        for source in SOURCES:
            rpc = Fake(source)
            rpc.mutate = lambda r: [row.update(file='secret', token='secret') for row in r[source.rows]]
            group = search_group(rpc, source, 'test two', page_size=2)
            self.assertEqual((group.state, group.total, len(group.hits)), ('ready', 3, 3))
            self.assertEqual(len(rpc.calls), 4)
            self.assertNotIn('secret', repr(group))
            self.assertEqual(rpc.calls[0][1]['filter']['and'][1]['value'], 'two')
            self.assertTrue(all(m == source.method for m, _ in rpc.calls))

    def test_truncation_explicit(self):
        group = search_group(Fake(count=100), SOURCES[0], 'title', page_size=2, cap=3)
        self.assertEqual(len(group.hits), 3)
        self.assertTrue(group.truncated)
        self.assertEqual(group.total, 100)

    def test_empty_is_not_unavailable(self):
        self.assertEqual(search_group(Fake(count=0), SOURCES[0], 'none').state, 'empty')
        def fail(*a): raise RuntimeError('token-in-error')
        group = search_group(fail, SOURCES[0], 'none')
        self.assertEqual(group.state, 'unavailable')
        self.assertNotIn('token', repr(group))

    def test_malformed_or_duplicate_fails_closed(self):
        mutations = [lambda r: r['limits'].update(total=True),
                     lambda r: r['limits'].update(end=999),
                     lambda r: r['tvshows'].pop(),
                     lambda r: r['tvshows'][0].update(tvshowid=True),
                     lambda r: r['tvshows'][0].update(tvshowid=-1),
                     lambda r: r['tvshows'][1].update(tvshowid=1),
                     lambda r: r['tvshows'][0].update(label='')]
        for mutation in mutations:
            rpc = Fake(); rpc.mutate = mutation
            group = search_group(rpc, SOURCES[0], 'a')
            self.assertEqual(group.state, 'unavailable')
            self.assertFalse(group.hits)

    def test_changes_between_reads_fail_closed(self):
        rpc = Fake()
        def mutate(result):
            if len(rpc.calls) > 1: result['tvshows'][0]['label'] = 'Changed'
        rpc.mutate = mutate
        self.assertEqual(search_group(rpc, SOURCES[0], 'a').state, 'unavailable')

    def test_artist_scalar_and_album_credit_array(self):
        rpc = Fake(SOURCES[3]); rpc.mutate = lambda r: r['artists'][0].update(artist='Name')
        self.assertEqual(search_group(rpc, SOURCES[3], 'a').state, 'ready')
        rpc = Fake(SOURCES[2]); rpc.mutate = lambda r: r['albums'][0].update(artist='Wrong shape')
        self.assertEqual(search_group(rpc, SOURCES[2], 'a').state, 'unavailable')

    def test_missing_artist_sentinel_excluded_at_native_filter_not_songs(self):
        for source in SOURCES:
            rpc=Fake(source);search_group(rpc,source,'a')
            filters=rpc.calls[0][1]['filter']
            if source.kind=='artist':
                self.assertIn(dict(field='artist',operator='isnot',value='[Missing Tag]'),filters['and'])
            else:self.assertEqual(filters,dict(field=source.field,operator='contains',value='a'))

    def test_cancel_aborts_not_empty(self):
        with self.assertRaisesRegex(SearchUnavailable, 'cancelled'):
            search_group(Fake(), SOURCES[0], 'a', cancelled=lambda: True)

    def test_bad_options(self):
        for kwargs in ({'page_size': True}, {'cap': 1}, {'cap': 2001}):
            with self.assertRaises(SearchUnavailable): search_group(Fake(), SOURCES[0], 'a', **kwargs)

    def test_group_failure_does_not_hide_other_sources(self):
        def rpc(method, params):
            if method == SOURCES[0].method: raise RuntimeError()
            source = next(s for s in SOURCES if s.method == method)
            return Fake(source)(method, params)
        groups = search(rpc, 'test')
        self.assertEqual([g.state for g in groups], ['unavailable']+['ready']*4)


if __name__ == '__main__': unittest.main()
