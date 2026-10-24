import copy
import unittest

from music_catalogue import (CatalogueUnavailable, TABLES, build_catalogue,
                             read_catalogue, read_pages)
from music_policy import OTHER


class FakeLibrary:
    def __init__(self):
        self.data = {
            'albums': [{'albumid':1,'label':'Rock album','genre':['Rock']},
                       {'albumid':2,'label':'Festive album','genre':['Christmas']}],
            'artists': [{'artistid':1,'label':'Main artist','genre':[]},
                        {'artistid':2,'label':'Guest artist','genre':[]}],
            'songs': [{'songid':1,'label':'Holiday in Cambodia','genre':['Rock'],
                       'albumid':1,'artistid':[1,2]},
                      {'songid':2,'label':'Winter','genre':['Jazz, Blues, R&B & Soul'],
                       'albumid':2,'artistid':[1]},
                      {'songid':3,'label':'Untagged','genre':[], 'artistid':[]}],
        }
        self.calls = []

    def __call__(self, method, params):
        self.calls.append((method, copy.deepcopy(params)))
        key = next(table[1] for table in TABLES if table[0] == method)
        start, end = params['limits']['start'], params['limits']['end']
        rows = copy.deepcopy(self.data[key][start:end])
        return {key: rows, 'limits': {'start':start,'end':start+len(rows),
                                    'total':len(self.data[key])}}


class CatalogueTests(unittest.TestCase):
    def test_canonical_missing_tag_is_not_a_named_artist_credit(self):
        fake=FakeLibrary();fake.data['artists'][0]['label']='[Missing Tag]'
        fake.data['songs'][0]['artistid']=[1]
        result=read_catalogue(fake)
        rock=next(row for row in result.categories() if row['label']=='Rock & Alternative')
        self.assertEqual(rock['uncredited_song_count'],1)
        self.assertEqual(rock['artist_count'],0)
        self.assertEqual(result.songs[1]['artistid'],[1])
        self.assertIn(1,result.shuffle_summary['eligible_ids'])
        self.assertEqual(result.browse('Rock & Alternative','song')['uncredited_song_count'],1)

    def test_live_boundary_only_calls_read_only_music_methods(self):
        fake=FakeLibrary(); before=copy.deepcopy(fake.data)
        result=read_catalogue(fake,page_size=2)
        self.assertEqual(fake.data,before)
        self.assertEqual({m for m,p in fake.calls},{t[0] for t in TABLES})
        self.assertTrue(all(p.get('albumartistsonly') is False
                            for m,p in fake.calls if m.endswith('GetArtists')))
        self.assertEqual(result.shuffle_summary['eligible_ids'],[1,3])
        self.assertEqual(result.shuffle_summary['excluded'],1)

    def test_genre_album_artist_and_song_memberships_follow_tracks(self):
        result=read_catalogue(FakeLibrary())
        rock=next(row for row in result.categories() if row['label']=='Rock & Alternative')
        self.assertEqual(rock,{'label':'Rock & Alternative','song_count':1,
                              'album_count':1,'artist_count':2,'uncredited_song_count':0})
        self.assertEqual(result.browse('Rock & Alternative','artist')['total'],2)
        self.assertEqual(result.browse(OTHER,'song')['rows'][0]['songid'],3)
        self.assertEqual(result.browse(OTHER,'artist')['uncredited_song_count'],1)
        # Holiday album exclusion affects Shuffle all, not genre browsing.
        self.assertEqual(result.browse('Jazz, Blues, R&B & Soul','album')['rows'][0]['albumid'],2)

    def test_browse_search_pagination_and_returned_rows_are_independent(self):
        result=read_catalogue(FakeLibrary())
        page=result.browse('Rock & Alternative','artist',limit=1)
        self.assertTrue(page['has_more'])
        self.assertEqual(result.browse('Rock & Alternative','artist',offset=1,limit=1)['rows'][0]['label'],'Main artist')
        self.assertEqual(result.browse('Rock & Alternative','song',query='CAMBODIA')['total'],1)
        page['rows'][0]['label']='Changed'
        self.assertEqual(result.browse('Rock & Alternative','artist',limit=1)['rows'][0]['label'],'Guest artist')

    def test_full_catalogue_is_not_truncated_to_500_songs(self):
        fake=FakeLibrary()
        fake.data['songs']=[{'songid':i+1,'label':str(i),'genre':['Rock'],
                             'albumid':1,'artistid':[1]} for i in range(17113)]
        result=read_catalogue(fake)
        self.assertEqual(len(result.songs),17113)
        self.assertEqual(len(result.shuffle_summary['eligible_ids']),17113)
        self.assertTrue(any(p['limits']['start']==17000 for m,p in fake.calls))

    def test_explicit_empty_library_is_not_a_failed_read(self):
        fake=FakeLibrary(); fake.data={key:[] for key in fake.data}
        result=read_catalogue(fake)
        self.assertEqual(result.shuffle_summary['total'],0)
        self.assertTrue(all(row['song_count']==0 for row in result.categories()))

    def test_unknown_response_fields_and_media_paths_are_not_retained(self):
        fake=FakeLibrary(); fake.data['songs'][0]['file']='private-media-path'
        fake.data['songs'][0]['unexpected']='private-value'
        result=read_catalogue(fake)
        self.assertNotIn('file',result.songs[1])
        self.assertNotIn('unexpected',result.songs[1])

    def test_kodi_explicit_zero_total_can_omit_the_empty_array(self):
        result=read_catalogue(lambda *args:{'limits':{'start':0,'end':0,'total':0}})
        self.assertEqual(len(result.songs),0)

    def test_raw_transport_errors_are_not_exposed(self):
        def fail(*args): raise RuntimeError('secret-bearing-network-error')
        with self.assertRaisesRegex(CatalogueUnavailable,'^library-read-failed$'):
            read_catalogue(fail)

    def test_missing_limits_and_rows_fail_instead_of_showing_empty(self):
        for response in ({},[],{'albums':[]},{'limits':{'total':0}}):
            with self.assertRaises(CatalogueUnavailable):
                read_pages(lambda *args:response,TABLES[0])

    def test_empty_intermediate_page_or_invalid_bounds_fail(self):
        for limits in ({'start':0,'end':0,'total':10},
                       {'start':1,'end':0,'total':0},
                       {'start':0,'end':1,'total':0},
                       {'start':0,'end':0,'total':True},
                       {'start':0,'end':0,'total':10001}):
            with self.assertRaises(CatalogueUnavailable):
                read_pages(lambda *args:{'albums':[],'limits':limits},TABLES[0])

    def test_duplicate_boolean_or_missing_id_fails(self):
        for rows in ([{'albumid':1},{'albumid':1}],
                     [{'albumid':True}], [{'label':'No identity'}]):
            fake=FakeLibrary();fake.data['albums']=rows
            with self.assertRaises(CatalogueUnavailable):read_catalogue(fake)

    def test_total_change_during_pagination_fails(self):
        fake=FakeLibrary()
        def mutate(method,params):
            result=fake(method,params)
            if method.endswith('GetSongs') and params['limits']['start']>0:
                result['limits']['total']+=1
            return result
        with self.assertRaisesRegex(CatalogueUnavailable,'library-changed-during-read'):
            read_catalogue(mutate,page_size=2)

    def test_same_count_tag_change_between_complete_reads_fails(self):
        fake=FakeLibrary(); calls=0
        def mutate(method,params):
            nonlocal calls
            if method.endswith('GetAlbums'):
                calls+=1
                if calls==2:fake.data['songs'][0]['genre']=['Christmas']
            return fake(method,params)
        with self.assertRaisesRegex(CatalogueUnavailable,'library-changed-during-verification'):
            read_catalogue(mutate)

    def test_missing_parent_or_guest_artist_is_not_silently_dropped(self):
        for key in ('albums','artists'):
            fake=FakeLibrary();fake.data[key]=fake.data[key][:1]
            with self.assertRaises(CatalogueUnavailable):read_catalogue(fake)

    def test_invalid_relationships_or_genre_types_fail(self):
        for patch in ({'albumid':True},{'artistid':'1'},{'artistid':[True]},
                      {'genre':'Rock'},{'genre':[123]}):
            fake=FakeLibrary();fake.data['songs'][0].update(patch)
            with self.assertRaises(CatalogueUnavailable):read_catalogue(fake)

    def test_invalid_browse_inputs_and_rpc_options_do_not_run(self):
        result=read_catalogue(FakeLibrary())
        for kwargs in ({'offset':-1},{'limit':0},{'limit':201},{'query':None}):
            with self.assertRaises(CatalogueUnavailable):result.browse('Christmas','song',**kwargs)
        with self.assertRaises(CatalogueUnavailable):result.browse('invented','song')
        with self.assertRaises(CatalogueUnavailable):result.browse('Christmas','play')
        for size in (0,-1,True,2001):
            with self.assertRaises(CatalogueUnavailable):read_pages(None,TABLES[0],page_size=size)

    def credit_join(self, fake, *, short_basic=False, mutate=False):
        def rpc(method,params):
            result=fake(method,params)
            if method.endswith('GetSongs'):
                if 'artistid' in params['properties']:
                    result['songs']=[r for r in result['songs'] if r.get('artistid')]
                elif short_basic:
                    result['songs']=result['songs'][:-1]
                elif mutate:
                    result['songs'][0]['genre']=['Christmas']
            return result
        return rpc

    def test_short_artist_join_recovers_full_basic_page_and_flags_missing_credit(self):
        fake=FakeLibrary()
        result=read_catalogue(self.credit_join(fake))
        self.assertEqual(len(result.songs),3)
        self.assertEqual(result.songs[3]['artistid'],[])
        self.assertFalse(result.songs[3]['artist_credit_available'])
        self.assertEqual(result.shuffle_summary['artist_unavailable_songs'],1)
        self.assertEqual(result.shuffle_summary['eligible_ids'],[1,3])

    def test_short_basic_page_is_never_accepted_as_complete(self):
        with self.assertRaisesRegex(CatalogueUnavailable,'incomplete-library-page'):
            read_catalogue(self.credit_join(FakeLibrary(),short_basic=True))

    def test_inconsistent_artist_and_basic_reads_fail_closed(self):
        with self.assertRaisesRegex(CatalogueUnavailable,'library-changed-during-read'):
            read_catalogue(self.credit_join(FakeLibrary(),mutate=True))

    def test_mass_credit_omissions_exceed_bound_instead_of_silent_repair(self):
        fake=FakeLibrary()
        fake.data['songs']=[{'songid':i+1,'genre':[],'artistid':[]} for i in range(129)]
        with self.assertRaises(CatalogueUnavailable):read_catalogue(self.credit_join(fake))


if __name__=='__main__':unittest.main()
